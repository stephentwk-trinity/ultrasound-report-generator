from loguru import logger
from pathlib import Path
import sys

class LoggerManager:
    """Configure application-wide logging"""

    def __init__(self, log_dir: Path, level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Remove default handler
        logger.remove()

        # Add console handler with colors
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )

        # Add file handler
        logger.add(
            self.log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=level,
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )

        # Add error file handler
        logger.add(
            self.log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="10 MB",
            retention="60 days",
            compression="zip"
        )

    @staticmethod
    def get_logger(name: str = __name__):
        """Get logger instance"""
        return logger.bind(name=name)

# Usage in other modules
# from src.utils.logger import LoggerManager
# logger = LoggerManager.get_logger(__name__)