import sys
import os
import os.path
import logging
from datetime import datetime


log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# In production/stage emit WARNING+; in dev emit everything.
_app_env = os.environ.get("APP_ENV", "dev")
_console_level = logging.DEBUG if _app_env == "dev" else logging.WARNING

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
console_handler.setLevel(_console_level)

# Optionally, create a file handler
log_file_name = f"app_{datetime.now().strftime('%Y%m%d')}.log"
log_file_path = os.path.join(os.environ.get("PROJECT_ROOT"), "log", log_file_name)

# Ensure the directory exists
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
file_handler.setFormatter(log_format)
file_handler.setLevel(_console_level)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # Logger itself always captures DEBUG so Sentry breadcrumbs get the full trail.
    # The console/file handlers above filter down to WARNING in prod.
    logger.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Keep propagate=True so Sentry's LoggingIntegration (attached to the root
    # logger) receives every record and stores DEBUG+ as breadcrumbs.
    # Duplicate output is prevented because only named handlers emit to console/file.
    logger.propagate = True

    return logger
