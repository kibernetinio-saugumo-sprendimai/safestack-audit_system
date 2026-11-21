"""Private runtime storage and descriptor-based reads of untrusted sources.

POSIX no-follow operations are required. Unsupported platforms fail closed.
"""
import os
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = Path(os.environ.get("SAFESTACK_RUNTIME_ROOT", APP_ROOT / "runtime")).absolute()


def _directory_flags():
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise OSError("SafeStack requires POSIX no-follow filesystem operations")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _parts(relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in {".", ".."} for p in path.parts):
        raise ValueError("expected a relative path without traversal")
    return path.parts


@contextmanager
def directory_fd(root, parts=(), *, create=False, private=False):
    """Keep each opened directory pinned while traversing child names."""
    flags = _directory_flags()
    root = Path(root)
    if create:
        root.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(root, flags)
    try:
        if private:
            if os.fstat(fd).st_uid != os.getuid():
                raise PermissionError("runtime directory is not owned by this user")
            os.fchmod(fd, 0o700)
        for part in parts:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
            if private:
                if os.fstat(fd).st_uid != os.getuid():
                    raise PermissionError("runtime subdirectory is not owned by this user")
                os.fchmod(fd, 0o700)
        yield fd
    finally:
        os.close(fd)


def read_regular(root, relative, limit):
    parts = _parts(relative)
    with directory_fd(root, parts[:-1]) as parent:
        return read_regular_fd(parent, parts[-1], limit)


def read_regular_fd(parent, name, limit):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(name, flags, dir_fd=parent)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("source must be a regular file with one link")
        if info.st_size > limit:
            raise ValueError("source exceeds byte limit")
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        if len(data) > limit or (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("source grew or changed during read")
    return data.decode("utf-8").replace("\r\n", "\n")


def write_private(relative, content, *, exclusive=False):
    """Publish a new inode, never truncate a caller-planted link target."""
    parts = _parts(relative)
    with directory_fd(RUNTIME_ROOT, parts[:-1], create=True, private=True) as parent:
        temporary = parts[-1] if exclusive else f".write-{secrets.token_hex(16)}"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if not exclusive:
                os.replace(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
        except BaseException:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            raise
    return str(RUNTIME_ROOT / relative)


def append_private(relative, content):
    parts = _parts(relative)
    with directory_fd(RUNTIME_ROOT, parts[:-1], create=True, private=True) as parent:
        fd = os.open(parts[-1], os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise PermissionError("unsafe append target")
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)


def prepare_database(name):
    """Initialize SQLite and reject pre-existing linked DB/journal files."""
    _parts(name)
    if len(Path(name).parts) != 1:
        raise ValueError("database name must be a basename")
    with directory_fd(RUNTIME_ROOT, create=True, private=True) as parent:
        for suffix in ("", "-wal", "-shm", "-journal"):
            flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
            if not suffix:
                flags |= os.O_CREAT
            try:
                fd = os.open(name + suffix, flags, 0o600, dir_fd=parent)
            except FileNotFoundError:
                continue
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                    raise PermissionError("unsafe database file")
                os.fchmod(fd, 0o600)
            finally:
                os.close(fd)
    return str(RUNTIME_ROOT / name)
