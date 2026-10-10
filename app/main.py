"""Точка входу API-процесу (композиція): Container -> обробники -> контролери -> FastAPI.

Запуск: uvicorn app.main:create_app --factory
"""
from __future__ import annotations

from fastapi import FastAPI


def create_app(config_path: str = "config.yaml") -> FastAPI:
    """1) load_settings + setup_logging
    2) lifespan: Container.start() / close()
    3) створити контролери з обробників Container і підключити їхні router
    4) register_exception_handlers, роздача статичного UI
    """
    raise NotImplementedError
