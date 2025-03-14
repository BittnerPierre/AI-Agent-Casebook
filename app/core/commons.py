import os
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.logger import logger
from core.base import SupportedModel

_ = load_dotenv(find_dotenv())

def _set_env(var: str, value: str):
    if not os.environ.get(var):
        os.environ[var] = value


# don't know why I must do this in debug mode
_set_env("OPENAI_API_TYPE", "openai")


def initiate_model(model_name: Optional[SupportedModel] = None,
                   temperature: float = 0.7, tags: Optional[list[str]] = None) -> Optional[BaseChatModel]:
    """
    Initialize the chat model based on the model type.

    :param model_name: The name of the model.
    :param temperature: The temperature of the model.
    :param tags: Tags to add to the run trace.
    :return: An instance of BaseChatModel or None if the model type is unsupported.
    """
    _model_name = model_name.value if model_name else SupportedModel.DEFAULT.value
    # self.model = model or SupportedModel.MISTRAL_LARGE  # Set a default if I need to
    if _model_name.startswith("gpt"):
        # naming of model parameter (alias) is inconsistent in mistral and openAI
        return ChatOpenAI(model=_model_name, temperature=temperature, tags=tags)
    elif (_model_name.startswith("mistral")
          or _model_name.startswith("ministral")
          or _model_name.startswith("open-mistral")):
        # naming of model parameter (alias) is inconsistent in mistral and openAI
        return ChatMistralAI(model_name=_model_name, temperature=temperature, tags=tags) #, api_key=mistral_api_key)
    elif _model_name.startswith("claude"):
        # naming of model parameter (alias) is inconsistent in mistral and openAI
        return init_chat_model(model_provider="anthropic", model=_model_name, temperature=temperature, tags=tags) #, api_key=mistral_api_key)
    logger.warning(f"Invalid or unsupported model type: {_model_name}")
    return None


def initiate_embeddings(model_name: Optional[SupportedModel] = None) -> Optional[Embeddings]:
    """
    Initialize the embeddings model based on the model type.

    :param model_name: The name of the model.
    :return: An instance of Embeddings or None if the model type is unsupported.
    """
    _model_name = model_name.value or None
    if _model_name.startswith("gpt"):
        return OpenAIEmbeddings()
    elif (_model_name.startswith("mistral")
          or _model_name.startswith("ministral")
          or _model_name.startswith("open-mistral")):
        return MistralAIEmbeddings()
    print(f"Invalid or unsupported model type for embeddings: {model_name}")
    return None

