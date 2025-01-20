# tests/conftest.py

import sys
import os

from configparser import ConfigParser
import pytest

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