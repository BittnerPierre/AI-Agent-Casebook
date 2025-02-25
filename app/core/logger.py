import logging

root_logger = logging.getLogger()


# Configure your main logger
root_logger.setLevel(logging.WARNING)  # Set your desired level (INFO, DEBUG, etc.)


# Suppress logging from specific third-party packages
# Replace 'some_external_package' with the actual package name(s)
# logging.getLogger('langchain_core').setLevel(logging.WARNING)
# logging.getLogger('langchain_openai').setLevel(logging.WARNING)
# logging.getLogger('langchain_mistralai').setLevel(logging.WARNING)
# logging.getLogger('langsmith').setLevel(logging.WARNING)
# logging.getLogger('httpcore').setLevel(logging.WARNING)
# logging.getLogger('pydantic').setLevel(logging.WARNING)
# logging.getLogger('dotenv').setLevel(logging.WARNING)
# logging.getLogger('httpx').setLevel(logging.WARNING)
# logging.getLogger('chromadb').setLevel(logging.WARNING)
# logging.getLogger('openai').setLevel(logging.WARNING)


def get_logger() -> logging.Logger:
    """
    Factory method to retrieve the default logger.
    This ensures that loggers are initialized with the same handlers and formatters.
    """
    return logging.getLogger(__name__)


def setup_logger(name: str, filepath: str, stream_level: int = logging.INFO,
                 file_level: int = logging.DEBUG) -> logging.Logger:
    __logger = logging.getLogger(name)
    if not __logger.hasHandlers():
        stream_handler = logging.StreamHandler()
        stream_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(stream_level)

        file_handler = logging.FileHandler(filepath)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(file_level)

        __logger.addHandler(stream_handler)
        __logger.addHandler(file_handler)
        __logger.setLevel(min(stream_level, file_level))
    return __logger


logger = setup_logger(__name__, './logs/app.log', stream_level=logging.INFO, file_level=logging.DEBUG)
