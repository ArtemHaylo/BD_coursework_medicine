"""Налаштування логування: рівень береться з конфігурації без зміни коду."""
from __future__ import annotations

from app.infrastructure.config.settings import LoggingSettings


def setup_logging(settings: LoggingSettings) -> None:
    """Підключає logging з рівнем ERROR / WARNING / INFO / DEBUG і єдиним форматом."""
    raise NotImplementedError
