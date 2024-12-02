from enum import Enum
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


class SupportedModel(Enum):
    GPT_4_O = "gpt-4o"
    # GPT_4_O_mini = "gpt-4o-mini" TODO Does not work
    MISTRAL_LARGE = "mistral-large-latest"
    DEFAULT = "mistral-large-latest" # "mistral-large-latest"


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
    elif _model_name.startswith("mistral"):
        return ChatMistralAI(model=_model_name, temperature=temperature) #, api_key=mistral_api_key)
    print(f"Invalid or unsupported model type: {_model_name}")
    return None


def initiate_embeddings(model: Optional[SupportedModel] = None) -> Optional[Embeddings]:
    """
    Initialize the embeddings model based on the model type.

    :param model: The name of the model.
    :return: An instance of Embeddings or None if the model type is unsupported.
    """
    model_name = model.value or None
    if model_name.startswith("gpt"):
        return OpenAIEmbeddings()
    elif model_name.startswith("mistral"):
        return MistralAIEmbeddings()
    print(f"Invalid or unsupported model type for embeddings: {model_name}")
    return None

