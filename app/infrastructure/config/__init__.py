"""Композиційний корінь (container.py).

Container навмисно не реекспортується тут: використовуйте
    from app.infrastructure.config.container import Container
Налаштування (Settings) лежать в app/infrastructure/settings.py, щоб адаптери
не залежали від композиційного кореня.
"""
from app.infrastructure.settings import Settings, load_settings

__all__ = ["Settings", "load_settings"]
