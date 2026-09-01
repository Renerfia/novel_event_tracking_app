import logging
from typing import Literal
from pathlib import Path

file_name = Path("logs/logs.log")

if not file_name.parent.exists():
    file_name.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',filename=file_name, filemode="a")
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def log(level: Literal["debug", "info", "warning", "error","critical"], message:str):
    """Logs a message with the specified type (info, warning, error)"""
    if level == "debug":
        logger.debug(message)
    elif level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
    else:
        logger.info(message)  # Default to info if unknown type