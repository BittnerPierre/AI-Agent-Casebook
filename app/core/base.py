from enum import Enum


class SupportedModel(Enum):
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    # GPT_4_O_mini = "gpt-4o-mini" TODO Does not work
    MISTRAL_LARGE = "mistral-large-latest"
    MINISTRAL_8B = "ministral-8b-latest"
    MISTRAL_NEMO = "open-mistral-nemo"
    MISTRAL_SMALL = "mistral-small-latest"
    MISTRAL_SMALL_2402 = "mistral-small-2402"
    DEFAULT = MISTRAL_SMALL
