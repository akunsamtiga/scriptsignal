#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║    Telegram Signal Bot — Multi-user          ║
║    /start → langsung terima sinyal           ║
╚══════════════════════════════════════════════╝
"""

import os
import json
import time
import random
import logging
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  Konfigurasi
# ─────────────────────────────────────────────
BOT_TOKEN       = os.getenv("BOT_TOKEN", "")
INTERVAL_MENIT  = int(os.getenv("INTERVAL_MENIT", "5"))
SUBSCRIBER_FILE = "subscribers.json"

# ─────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("signal_bot")


# ─────────────────────────────────────────────
#  Manajemen Subscriber  (thread-safe)
# ─────────────────────────────────────────────
_lock = threading.Lock()
_subscribers: set = set()


def _load() -> set:
    try:
        with open(SUBSCRIBER_FILE, "r") as f:
            return set(json.load(f).get("chat_ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save():
    """Harus dipanggil saat _lock sudah dipegang."""
    with open(SUBSCRIBER_FILE, "w") as f:
        json.dump({"chat_ids": list(_subscribers)}, f, indent=2)


def add_subscriber(chat_id: int) -> bool:
    """Tambah subscriber. Return True jika baru, False jika sudah ada."""
    with _lock:
        if chat_id in _subscribers:
            return False
        _subscribers.add(chat_id)
        _save()
        return True


def remove_subscriber(chat_id: int) -> bool:
    """Hapus subscriber. Return True jika berhasil."""
    with _lock:
        if chat_id not in _subscribers:
            return False
        _subscribers.discard(chat_id)
        _save()
        return True


def is_subscriber(chat_id: int) -> bool:
    with _lock:
        return chat_id in _subscribers


def get_subscribers() -> list:
    with _lock:
        return list(_subscribers)


def count_subscribers() -> int:
    with _lock:
        return len(_subscribers)


# ─────────────────────────────────────────────
#  Telegram API
# ─────────────────────────────────────────────
def send_message(chat_id: int, text: str, retries: int = 3) -> bool:
    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=data, timeout=10)

            # User blokir bot → hapus otomatis dari daftar
            if r.status_code == 403:
                log.info("User %s blokir bot → otomatis dihapus", chat_id)
                remove_subscriber(chat_id)
                return False

            r.raise_for_status()
            return True

        except requests.RequestException as e:
            log.warning("Kirim ke %s gagal (percobaan %d/%d): %s", chat_id, attempt, retries, e)
            if attempt < retries:
                time.sleep(3 * attempt)

    return False


def broadcast(text: str):
    """Kirim pesan ke semua subscriber sekaligus."""
    subs = get_subscribers()
    if not subs:
        log.info("Tidak ada subscriber, sinyal dilewati.")
        return

    log.info("📡  Broadcast [%s] ke %d subscriber", text, len(subs))
    for chat_id in subs:
        send_message(chat_id, text)


# ─────────────────────────────────────────────
#  Generator Sinyal
# ─────────────────────────────────────────────
def generate_signal() -> str:
    """
    Ganti isi fungsi ini untuk logika sinyal kustom.
    Default: random B atau S.
    """
    return random.choice(["B", "S"])


# ─────────────────────────────────────────────
#  Timing — aligned ke jam
# ─────────────────────────────────────────────
def detik_ke_interval_berikutnya() -> float:
    ts      = datetime.now().timestamp()
    periode = INTERVAL_MENIT * 60
    sisa    = periode - (ts % periode)
    return sisa if sisa > 0.5 else periode   # minimum 0.5 detik


# ─────────────────────────────────────────────
#  Command Handler
# ─────────────────────────────────────────────
def handle_updates(updates: list, last_id: int) -> int:
    for update in updates:
        uid = update["update_id"]
        if uid <= last_id:
            continue
        last_id = uid

        msg     = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text    = msg.get("text", "").strip()
        name    = msg.get("from", {}).get("first_name", "User")

        if not chat_id or not text:
            continue

        cmd = text.split("@")[0].lower()   # abaikan @botname suffix

        # ── /start ──────────────────────────────
        if cmd == "/start":
            baru = add_subscriber(chat_id)
            log.info("👤 /start dari %s (%s) — %s", name, chat_id,
                     "BARU" if baru else "sudah terdaftar")

            if baru:
                send_message(chat_id,
                    f"✅ <b>Halo, {name}!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Kamu sudah <b>subscribe</b> sinyal trading.\n\n"
                    f"⏱  Sinyal dikirim setiap <b>{INTERVAL_MENIT} menit</b>\n"
                    f"📌  Format:  <code>12:40 B</code>  atau  <code>12:45 S</code>\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Ketik /stop untuk berhenti menerima sinyal."
                )
            else:
                send_message(chat_id,
                    f"ℹ️ <b>{name}</b>, kamu sudah terdaftar sebelumnya.\n"
                    f"Sinyal dikirim otomatis setiap <b>{INTERVAL_MENIT} menit</b>.\n\n"
                    "Ketik /stop untuk berhenti."
                )

        # ── /stop ───────────────────────────────
        elif cmd == "/stop":
            ada = remove_subscriber(chat_id)
            log.info("👤 /stop dari %s (%s)", name, chat_id)

            if ada:
                send_message(chat_id,
                    f"❌ <b>{name}</b>, kamu sudah <b>unsubscribe</b>.\n"
                    "Sinyal tidak akan dikirim lagi.\n\n"
                    "Ketik /start kapan saja untuk subscribe kembali."
                )
            else:
                send_message(chat_id,
                    "ℹ️ Kamu memang belum subscribe.\n"
                    "Ketik /start untuk mulai menerima sinyal."
                )

        # ── /status ─────────────────────────────
        elif cmd == "/status":
            aktif = is_subscriber(chat_id)
            total = count_subscribers()
            send_message(chat_id,
                f"📊 <b>Status Kamu</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{'✅ Aktif — menerima sinyal' if aktif else '❌ Tidak aktif'}\n\n"
                f"👥 Total subscriber: <b>{total}</b>\n"
                f"⏱  Interval: <b>{INTERVAL_MENIT} menit</b>"
            )

    return last_id


# ─────────────────────────────────────────────
#  Thread 1: Long Polling (terima command)
# ─────────────────────────────────────────────
def polling_loop():
    last_id = 0
    log.info("▶️   Polling thread dimulai...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            r   = requests.get(url,
                               params={"offset": last_id + 1, "timeout": 30},
                               timeout=35)
            r.raise_for_status()
            updates = r.json().get("result", [])
            if updates:
                last_id = handle_updates(updates, last_id)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error("Polling error: %s — retry 5 detik...", e)
            time.sleep(5)


# ─────────────────────────────────────────────
#  Thread 2: Signal Scheduler (kirim sinyal)
# ─────────────────────────────────────────────
def signal_loop():
    log.info("▶️   Signal scheduler dimulai...")

    while True:
        try:
            tunggu = detik_ke_interval_berikutnya()
            waktu_next = datetime.fromtimestamp(
                datetime.now().timestamp() + tunggu
            ).strftime("%H:%M")

            log.info("⏳  Sinyal berikutnya jam %s (dalam %.0f detik)", waktu_next, tunggu)
            time.sleep(tunggu)

            jam_str = datetime.now().strftime("%H:%M")
            sinyal  = generate_signal()
            broadcast(f"{jam_str} {sinyal}")

            time.sleep(3)   # anti double-fire

        except Exception as e:
            log.error("Scheduler error: %s — retry 10 detik...", e)
            time.sleep(10)


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        log.critical("BOT_TOKEN kosong — edit file .env!")
        raise SystemExit(1)

    # Muat subscriber yang tersimpan
    global _subscribers
    _subscribers = _load()

    log.info("=" * 52)
    log.info("🤖  Signal Bot — Multi-user Subscription")
    log.info("    Interval         : %d menit", INTERVAL_MENIT)
    log.info("    Subscriber aktif : %d", count_subscribers())
    log.info("=" * 52)

    # Polling di thread terpisah (daemon → ikut mati saat main selesai)
    t = threading.Thread(target=polling_loop, daemon=True, name="polling")
    t.start()

    # Scheduler di main thread
    try:
        signal_loop()
    except KeyboardInterrupt:
        log.info("🛑  Bot dihentikan manual (Ctrl+C)")


if __name__ == "__main__":
    main()