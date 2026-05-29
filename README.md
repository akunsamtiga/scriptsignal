# 🤖 Telegram Signal Bot

Bot Telegram sinyal trading **Buy (B) / Sell (S)** otomatis setiap 5 menit.
User cukup buka bot → ketik `/start` → langsung terima sinyal. Berjalan **24 jam non-stop** di Ubuntu VPS via systemd.

---

## 📋 Format Sinyal yang Diterima User

```
12:40 B
12:45 B
12:50 S
12:55 B
13:00 S
```

`B` = Buy  |  `S` = Sell — dikirim tepat di menit `:00 :05 :10 ... :55`

---

## 💬 Command untuk User

| Command | Fungsi |
|---------|--------|
| `/start` | Subscribe — mulai terima sinyal otomatis |
| `/stop` | Unsubscribe — berhenti terima sinyal |
| `/status` | Cek status & total subscriber |

---

## 📁 Struktur File

```
telegram-signal-bot/
├── bot.py              # Bot utama
├── requirements.txt    # Dependensi Python
├── .env.example        # Template konfigurasi
├── .gitignore          # File yang tidak masuk Git
├── install.sh          # Script setup otomatis (jalankan 1x di VPS)
├── update.sh           # Script update dari Git
└── README.md           # Dokumentasi ini
```

---

## ⚙️ Persiapan — Buat Bot via BotFather

1. Buka Telegram → cari **@BotFather**
2. Kirim `/newbot` → ikuti instruksi → beri nama bot
3. Salin **Bot Token** yang diberikan (format: `1234567890:ABCdef...`)

> Tidak perlu CHAT_ID — subscriber dikelola otomatis saat user `/start`

---

## 🚀 Deploy ke VPS Ubuntu

### Langkah 1 — Push ke Git (dari lokal)

```bash
git init
git add .
git commit -m "init signal bot"
git remote add origin https://github.com/USERNAME/telegram-signal-bot.git
git push -u origin main
```

### Langkah 2 — Clone di VPS

```bash
ssh root@IP_VPS_KAMU

git clone https://github.com/USERNAME/telegram-signal-bot.git /opt/telegram-signal-bot
cd /opt/telegram-signal-bot
```

### Langkah 3 — Install otomatis

```bash
sudo bash install.sh
```

Script ini akan: install Python3 + pip, install packages, daftarkan sebagai systemd service.

### Langkah 4 — Isi konfigurasi

```bash
nano /opt/telegram-signal-bot/.env
```

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
INTERVAL_MENIT=5
```

Simpan: `Ctrl+X` → `Y` → `Enter`

### Langkah 5 — Jalankan bot

```bash
systemctl start signal-bot
systemctl status signal-bot
```

---

## 📡 Manajemen Bot di VPS

```bash
systemctl start signal-bot        # Jalankan
systemctl stop signal-bot         # Hentikan
systemctl restart signal-bot      # Restart
systemctl status signal-bot       # Cek status

journalctl -u signal-bot -f       # Log realtime
journalctl -u signal-bot -n 50    # 50 baris log terakhir
```

---

## 🔄 Update dari Git

Setelah push perubahan ke repository:

```bash
sudo bash /opt/telegram-signal-bot/update.sh
```

Otomatis: `git pull` → update packages → restart service.

---

## 🛠️ Kustomisasi Sinyal

Edit fungsi `generate_signal()` di `bot.py`:

```python
def generate_signal() -> str:
    # Default: random 50/50
    return random.choice(["B", "S"])

    # Contoh berbasis jam:
    # jam = datetime.now().hour
    # return "B" if 8 <= jam < 12 else "S"
```

Setelah edit → `git push` → `sudo bash update.sh` di VPS.

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Bot tidak respon `/start` | Cek BOT_TOKEN di `.env` |
| Service gagal start | `journalctl -u signal-bot -n 30` |
| Sinyal tidak terkirim | Pastikan user sudah `/start`, cek log |
| Bot berhenti sendiri | Systemd auto-restart dalam 10 detik |