import logging
import sys
from loguru import logger
from app.core.config import get_settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect them to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Configures structured logging for the application and standard libraries."""
    settings = get_settings()

    # Remove all existing handlers
    logger.remove()

    # Add stdout handler with rich formatting
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format=log_format,
        colorize=True,
        enqueue=True,
    )

    # Intercept standard library loggers (uvicorn, fastapi, sqlalchemy)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy.engine"):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False


# Default logger export
__all__ = ["logger", "setup_logging"]
