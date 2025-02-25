import os
from configparser import ConfigParser


def is_test_mode():
    """
    Detect if the application is running in test mode.
    This can be based on pytest being invoked or a specific environment variable.
    """
    return 'PYTEST_CURRENT_TEST' in os.environ or 'TEST_MODE' in os.environ


def load_config(config_path=None, defaults=None):
    """
    Load configuration from the specified path. If no path is provided, it defaults
    to the main config file in the source package.

    :param config_path: Path to the configuration file.
    :param defaults: Optional dictionary of default values.
    :return: ConfigParser instance.
    """
    config = ConfigParser()

    # Load default values if provided
    if defaults:
        config.read_dict(defaults)

    # Determine the config file path
    if not config_path:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        if is_test_mode():
            # Default to tests/test_config.ini
            config_path = os.path.join(project_root, "tests/test_config.ini")
        else:
            # Default to app/config.ini
            config_path = os.path.join(project_root, "app/config.ini")

    # Load the configuration file if it exists
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        print(f"Warning: Configuration file {config_path} not found. Using defaults.")

    return config
