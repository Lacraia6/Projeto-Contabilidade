"""Application configuration module."""

from __future__ import annotations

import os
from typing import Dict, Type


class BaseConfig:
	"""Default configuration shared across environments."""

	SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
	AUTH_ENABLED = True
	SQLALCHEMY_DATABASE_URI = os.getenv(
		'DATABASE_URL',
		'mysql+pymysql://root:Tuta1305*@localhost/contabilidade?charset=utf8mb4'
	)
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
	REDIS_URL = os.getenv('REDIS_URL') or os.getenv('CACHE_REDIS_URL')
	CACHE_TYPE = 'RedisCache' if REDIS_URL else 'simple'
	CACHE_REDIS_URL = REDIS_URL
	RATELIMIT_ENABLED = True
	RATELIMIT_STORAGE_URL = REDIS_URL or 'memory://'
	WTF_CSRF_ENABLED = True
	DEBUG = False
	TESTING = False


class DevelopmentConfig(BaseConfig):
	"""Configuration for local development."""

	DEBUG = True


class TestingConfig(BaseConfig):
	"""Configuration used during automated tests."""

	TESTING = True
	AUTH_ENABLED = False
	SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
	CACHE_TYPE = 'null'
	CACHE_REDIS_URL = None
	RATELIMIT_ENABLED = False
	RATELIMIT_STORAGE_URL = 'memory://'
	WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
	"""Configuration for production deployment."""

	DEBUG = False


CONFIG_BY_NAME: Dict[str, Type[BaseConfig]] = {
	'development': DevelopmentConfig,
	'dev': DevelopmentConfig,
	'testing': TestingConfig,
	'test': TestingConfig,
	'production': ProductionConfig,
	'prod': ProductionConfig,
}


def get_config(name: str | None) -> Type[BaseConfig]:
	"""Return configuration class for a given environment name."""

	if not name:
		return BaseConfig

	return CONFIG_BY_NAME.get(name.lower(), BaseConfig)


