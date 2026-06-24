"""Centralized rotating log configuration."""

from __future__ import annotations

import logging
import os
import time
from logging.handlers import RotatingFileHandler

from elysium.core.paths import get_app_log_path, get_logs_dir

DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def setup_logger(
    name: str = "Elysium",
    *,
    log_filename: str | None = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level)
    logging.raiseExceptions = False

    if log.handlers:
        return log

    formatter = logging.Formatter(DEFAULT_FORMAT)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)

    if log_filename:
        log_dir = get_logs_dir()
        log_path = os.path.join(log_dir, log_filename)
        _attach_rotating_handler(log, log_path, formatter)

    return log


def setup_dependency_logger(level: int = logging.INFO) -> logging.Logger:
    log = logging.getLogger("ElysiumDependencyManager")
    log.setLevel(level)
    logging.raiseExceptions = False

    if any(isinstance(h, RotatingFileHandler) for h in log.handlers):
        return log

    if not log.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        log.addHandler(console_handler)

    log_path = os.path.join(get_logs_dir(), f"dependency_log_{os.getpid()}.log")
    formatter = logging.Formatter(DEFAULT_FORMAT)

    for attempt in range(3):
        try:
            _attach_rotating_handler(log, log_path, formatter)
            break
        except OSError:
            if attempt < 2:
                time.sleep(1)
            else:
                log.warning(
                    "Could not set up file logging (file may be locked). "
                    "Continuing with console logging only."
                )

    return log


def get_app_logger(app_id: str, level: int = logging.INFO) -> logging.Logger:
    name = f"Elysium.App.{app_id}"
    log = logging.getLogger(name)
    log.setLevel(level)
    if log.handlers:
        return log
    formatter = logging.Formatter(DEFAULT_FORMAT)
    _attach_rotating_handler(log, get_app_log_path(app_id), formatter)
    return log


def _attach_rotating_handler(
    log: logging.Logger,
    log_path: str,
    formatter: logging.Formatter,
) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
