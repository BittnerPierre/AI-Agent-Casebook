import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

_ = load_dotenv(find_dotenv())

def _set_env(var: str, value: str):
    if not os.environ.get(var):
        os.environ[var] = value

# don't know why I must do this in debug mode
_set_env("OPENAI_API_TYPE", "openai")

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class SupportedModel(Enum):
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    # GPT_4_O_mini = "gpt-4o-mini" TODO Does not work
    MISTRAL_LARGE = "mistral-large-latest"
    MINISTRAL_8B = "ministral-8b-latest"
    MISTRAL_NEMO = "open-mistral-nemo"
    MISTRAL_SMALL = "mistral-small-latest"
    DEFAULT = GPT_4_O


def initiate_model(model_name: Optional[SupportedModel] = None,
                   temperature: float = 0.7) -> Optional[BaseChatModel]:
    """
    Initialize the chat model based on the model type.

    :param model_name: The name of the model.
    :param temperature: The temperature of the model.
    :return: An instance of BaseChatModel or None if the model type is unsupported.
    """
    _model_name = model_name.value if model_name else SupportedModel.DEFAULT.value
    # self.model = model or SupportedModel.MISTRAL_LARGE  # Set a default if I need to
    if _model_name.startswith("gpt"):
        return ChatOpenAI(model=_model_name, temperature=temperature)
    elif (_model_name.startswith("mistral")
          or _model_name.startswith("ministral")
          or _model_name.startswith("open-mistral")):
        return ChatMistralAI(model=_model_name, temperature=temperature) #, api_key=mistral_api_key)
    print(f"Invalid or unsupported model type: {_model_name}")
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

