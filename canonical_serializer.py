import json

def canonical_json(data: dict) -> str:
    """Creates deterministic serialization for reproducible hashing."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    )
