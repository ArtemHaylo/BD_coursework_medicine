"""Налаштування застосунку: адреси БД, логування, параметри пакетів і черги.

Читаються з config.yaml; змінні середовища (.env) мають вищий пріоритет.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MongoSettings:
    uri: str = "mongodb://localhost:27017"   # адреса mongos
    database: str = "medicine"


@dataclass
class ElasticSettings:
    url: str = "http://localhost:9200"
    index: str = "medicines"


@dataclass
class Neo4jSettings:
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "change_me"


@dataclass
class RedisSettings:
    url: str = "redis://localhost:6379"
    search_ttl_seconds: int = 60


@dataclass
class RabbitSettings:
    url: str = "amqp://guest:guest@localhost:5672/"
    queue: str = "medicine.ingest"
    prefetch: int = 10
    max_length: int = 1000          # обмеження довжини черги


@dataclass
class IngestSettings:
    batch_size: int = 5000


@dataclass
class LoggingSettings:
    level: str = "INFO"             # ERROR / WARNING / INFO / DEBUG


@dataclass
class Settings:
    mongo: MongoSettings = field(default_factory=MongoSettings)
    elastic: ElasticSettings = field(default_factory=ElasticSettings)
    neo4j: Neo4jSettings = field(default_factory=Neo4jSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    rabbit: RabbitSettings = field(default_factory=RabbitSettings)
    ingest: IngestSettings = field(default_factory=IngestSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)


def load_settings(path: str | Path = "config.yaml") -> Settings:
    """Читає YAML, накладає змінні середовища, повертає Settings."""
    raise NotImplementedError
