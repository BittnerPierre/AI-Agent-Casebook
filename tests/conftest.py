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


def pytest_configure():
    # Set global logging level
    # root_logger = logging.getLogger()

    # if not root_logger.hasHandlers():  # Prevent duplicate handlers
    #     logging.basicConfig(
    #         level=logging.INFO,
    #         format="%(asctime)s [%(levelname)s] %(message)s",
    #         datefmt="%Y-%m-%d %H:%M:%S",
    #     )

    # Suppress logging from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Example for HTTPX
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Example for requests
    logging.getLogger("mistral.ai").setLevel(logging.WARNING)  # Adjust this if needed


@pytest.fixture
def logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger