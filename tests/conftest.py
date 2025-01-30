# tests/conftest.py
import logging
import sys
import os

from configparser import ConfigParser
import pytest

from app.core.logger import setup_dual_logger

from dotenv import load_dotenv, find_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_ = load_dotenv(find_dotenv())


from app.core.config_loader import load_config

@pytest.fixture
def config():
    # Use test-specific config file
    test_config_path = os.path.join(os.path.dirname(__file__), "test_config.ini")
    return load_config(config_path=test_config_path)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    setup_dual_logger('AI-Agent-Casebook', './logs/test.log', stream_level=logging.INFO, file_level=logging.DEBUG)