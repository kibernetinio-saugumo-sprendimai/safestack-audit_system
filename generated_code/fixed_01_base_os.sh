```bash
#!/bin/bash

# 01_base_os.sh
# Post-installation checks and setup for SafeStack on Raspberry Pi 5
# Corresponds to install/01_base_os.md

set -euo pipefail

TARGET_USER="${TARGET_USER:-gizma}"
TARGET_HOSTNAME="${TARGET_HOSTNAME:-vpn}"

echo "🔍 Checking if user '$TARGET_USER' exists..."
if id "$TARGET_USER" &>/dev/null; then
  echo "✅ User '$TARGET_USER' exists."
else
  echo "❌ User '$TARGET_USER' not found!"
fi

echo "🔍 Checking SSH service status..."
if systemctl is-active --quiet ssh; then
  echo "✅ SSH is running."
else
  echo "❌ SSH is not running. Attempting to start..."
  if systemctl start ssh &>/dev/null; then
    echo "✅ SSH started."
  else
    echo "❌ Failed to start SSH."
  fi
fi

echo "🔍 Verifying hostname..."
current_hostname=$(hostname)
if [ "$current_hostname" != "$TARGET_HOSTNAME" ]; then
  echo "❌ Hostname is '$current_hostname', setting to '$TARGET_HOSTNAME'..."
  hostnamectl set-hostname "$TARGET_HOSTNAME"
  echo "✅ Hostname set to '$TARGET_HOSTNAME'. Reboot required to take full effect."
else
  echo "✅ Hostname is already '$TARGET_HOSTNAME'."
fi

echo "🔍 Checking if eth0 interface is up..."
if ip link show eth0 | grep -q "state UP"; then
  echo "✅ eth0 is up."
else
  echo "❌ eth0 is down or not found!"
fi

echo "📦 Diegiama SSD ir SD kortelių tausojimo technologija (ZRAM + fstrim)..."
# Diegiame zram-tools, kad OS nenaudotų fizinio disko virtualiai atminčiai (Swap)
apt-get install -y zram-tools &>/dev/null

# Konfigūruojame ZRAM naudoti modernų 'zstd' suspaudimą ir leisti naudoti 50% RAM
sed -i 's/^#*ALGO=.*/ALGO=zstd/' /etc/default/zramswap
sed -i 's/^#*PERCENT=.*/PERCENT=50/' /etc/default/zramswap
systemctl restart zramswap &>/dev/null || true

# Išjungiame fizinį Swap failą, kad nedrožtų SSD kortelės!
swapoff -a &>/dev/null || true
if [ -f /swap.img ]; then
  rm -f /swap.img
  sed -i '/swap.img/d' /etc/fstab
fi

# Įjungiame fstrim, kad SSD greitis laikui bėgant nekristų
systemctl enable --now fstrim.timer &>/dev/null || true

echo "✅ Base OS post-install and disk optimizations completed."
```