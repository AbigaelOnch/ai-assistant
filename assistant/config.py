import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _path(name: str, default: str) -> Path:
    p = Path(os.getenv(name, default)).expanduser()
    return p if p.is_absolute() else ROOT / p


MODEL = os.getenv("ASSISTANT_MODEL", "claude-sonnet-5-5")
ENABLED_TOOLS = {t.strip() for t in os.getenv(
    "ENABLED_TOOLS", "gmail,outlook,linkedin,notes,imessage,tasks").split(",") if t.strip()}

DATA_DIR = _path("DATA_DIR", "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "assistant.db"

PROFILE_PATH = ROOT / "profile.md"
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "24"))
NOTIFY = os.getenv("NOTIFY", "true").lower() == "true"

GMAIL_CREDENTIALS_FILE = _path("GMAIL_CREDENTIALS_FILE", "secrets/gmail_credentials.json")
GMAIL_TOKEN_FILE = _path("GMAIL_TOKEN_FILE", "secrets/gmail_token.json")

MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
MS_TENANT = os.getenv("MS_TENANT", "common")
MS_TOKEN_CACHE = _path("MS_TOKEN_CACHE", "secrets/ms_token_cache.json")
