"""Logging configuration for CLI entrypoint."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_file_path: str) -> None:
    Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
