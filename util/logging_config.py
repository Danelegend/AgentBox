import logging
import os
from logging.handlers import RotatingFileHandler


def configure_logging(
    log_path: str = "logs/app.log",
    level: int = logging.INFO,
    max_bytes: int = 5_000_000,
    backup_count: int = 5,
    include_console: bool = True,
):
    """
    Configure application-wide logging to write to a rotating file and (optionally) console.
    Safe to call multiple times; handlers will not be duplicated.
    """
    folder = os.path.dirname(log_path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure file handler exists (avoid duplicates across reloads)
    abs_log_path = os.path.abspath(log_path)
    has_file_handler = False
    for handler in root_logger.handlers:
        base = getattr(handler, "baseFilename", None)
        if base and os.path.abspath(base) == abs_log_path:
            has_file_handler = True
            break

    if not has_file_handler:
        file_handler = RotatingFileHandler(
            abs_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Optional console handler (avoid duplicates)
    if include_console:
        has_console = any(
            isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename")
            for h in root_logger.handlers
        )
        if not has_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)


