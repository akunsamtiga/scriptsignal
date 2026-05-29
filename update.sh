#!/bin/bash
# ────────────────────────────────────────────────────────────
#  update.sh — Pull update dari Git & restart service
#  Usage: sudo bash update.sh
# ────────────────────────────────────────────────────────────
set -e

SERVICE="signal-bot"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     Telegram Signal Bot — Update             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌  Jalankan sebagai root: sudo bash update.sh"
    exit 1
fi

# ── 1. Pull dari Git ─────────────────────────────────────────
echo "🔄  Mengambil update dari Git..."
cd "$SCRIPT_DIR"
git pull origin main
echo ""

# ── 2. Update Python packages ────────────────────────────────
echo "🐍  Mengupdate Python packages..."
pip3 install -r requirements.txt -q
echo "    ✅ Packages diperbarui"
echo ""

# ── 3. Restart service ───────────────────────────────────────
echo "🔁  Merestart service $SERVICE..."
systemctl restart "$SERVICE"
sleep 2

# ── 4. Status ────────────────────────────────────────────────
echo ""
systemctl status "$SERVICE" --no-pager -l
echo ""
echo "✅  Update selesai!"
echo "    Log realtime: journalctl -u $SERVICE -f"
echo ""