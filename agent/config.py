"""Runtime constants for the autonomous agent."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
DB_FILE = DATA_DIR / "agent.sqlite3"
CHANGE_LOG_FILE = LOG_DIR / "changes.log"
TARGET_SELF_MOD_FILE = PROJECT_ROOT / "agent" / "response_profile.py"

MODIFICATION_INTERVAL_TURNS = 6
MAX_MEMORY_ITEMS = 200
MAX_CODE_REVISIONS = 100
