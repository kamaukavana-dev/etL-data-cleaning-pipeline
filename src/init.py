import os
import logging
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Create root logger
logger = logging.getLogger(__name__)

# ✅ Rotating file handler (prevents huge logs, keeps history)
file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, "app.log"),
    maxBytes=5_000_000,   # ~5 MB per file
    backupCount=5         # keep 5 backups
)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ✅ Optional console logging (enabled if DEBUG=true in .env)
if os.getenv("DEBUG", "false").lower() == "true":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

logger.setLevel(logging.INFO)

# ✅ Package version constant for traceability
PACKAGE_VERSION = "1.0"

# ✅ Explicitly define what’s exposed when importing `src`
__all__ = ["PACKAGE_VERSION"]