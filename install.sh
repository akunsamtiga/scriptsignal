#!/bin/bash
# ────────────────────────────────────────────────────────────
#  install.sh — Setup Telegram Signal Bot di Ubuntu VPS
#  Jalankan SATU KALI setelah git clone
#  Usage: sudo bash install.sh
# ────────────────────────────────────────────────────────────
set -e

SERVICE="signal-bot"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     Telegram Signal Bot — Installer          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Cek root ──────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "❌  Jalankan sebagai root:"
    echo "    sudo bash install.sh"
    exit 1
fi

echo "📁  Direktori instalasi : $SCRIPT_DIR"
echo ""

# ── 2. Install dependensi sistem ─────────────────────────────
echo "📦  Menginstall Python3 & pip..."
apt-get update -qq
apt-get install -y python3 python3-pip git -qq
echo "    ✅ Python $(python3 --version)"

# ── 3. Install Python packages ───────────────────────────────
echo ""
echo "🐍  Menginstall Python packages..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" -q
echo "    ✅ Packages terinstall"

# ── 4. Setup .env ────────────────────────────────────────────
echo ""
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "📝  File .env dibuat dari .env.example"
else
    echo "📝  File .env sudah ada, tidak ditimpa"
fi

# ── 5. Install systemd service ───────────────────────────────
echo ""
echo "⚙️   Menginstall systemd service..."

# Generate service file dengan path yang benar
cat > /etc/systemd/system/"$SERVICE".service <<EOF
[Unit]
Description=Telegram Signal Bot - Sinyal Trading Otomatis
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/bot.py
Restart=always
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"
echo "    ✅ Service '$SERVICE' terdaftar & akan auto-start saat reboot"

# ── 6. Ringkasan ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅  Instalasi Selesai!                      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🔧  Langkah selanjutnya:"
echo ""
echo "   1) Isi konfigurasi bot:"
echo "      nano $SCRIPT_DIR/.env"
echo ""
echo "   2) Jalankan bot:"
echo "      systemctl start $SERVICE"
echo ""
echo "   3) Cek status:"
echo "      systemctl status $SERVICE"
echo ""
echo "   4) Lihat log realtime:"
echo "      journalctl -u $SERVICE -f"
echo ""