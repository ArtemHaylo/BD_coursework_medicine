"""Композиційний корінь і налаштування.

Container навмисно не реекспортується тут: він імпортує всі адаптери, а адаптери
(наприклад, logging_config) імпортують settings з цього пакета -> був би цикл.
Використовуйте: from app.infrastructure.config.container import Container
"""
from app.infrastructure.config.settings import Settings, load_settings

__all__ = ["Settings", "load_settings"]
