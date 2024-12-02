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

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


logger = setup_logger(__name__, level=logging.INFO)
