import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Отдельный токен именно для бота-ретранслятора.
# Нельзя использовать один и тот же токен в двух polling-процессах.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", os.getenv("BOT_TOKEN", "")).strip()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

def _parse_ids(raw: str) -> set[int]:
    out = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            out.add(int(part))
    return out

# Необязательно. Если пусто — бот пересылает из всех каналов, где он администратор.
SOURCE_CHANNEL_IDS = _parse_ids(os.getenv("SOURCE_CHANNEL_IDS", ""))

MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "24") or 24)
PORT = int(os.getenv("PORT", "0") or 0)
DROP_PENDING_UPDATES = os.getenv("DROP_PENDING_UPDATES", "1") == "1"
