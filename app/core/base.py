from enum import Enum


class SupportedModel(Enum):
    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_5_MINI = "gpt-5-mini"
    MISTRAL_LARGE = "mistral-large-latest"
    MINISTRAL_8B = "ministral-8b-latest"
    MISTRAL_NEMO = "open-mistral-nemo"
    MISTRAL_SMALL = "mistral-small-latest"
    MISTRAL_MEDIUM = "mistral-medium-latest"
    MISTRAL_SMALL_2402 = "mistral-small-2402"
    CLAUDE_SONNET_3_7 = "claude-3-7-sonnet-latest"
    CLAUDE_HAIKU_3_5 = "claude-3-5-haiku-latest"
    CLAUDE_SONNET_4_O = "claude-sonnet-4-0"
    DEFAULT = MISTRAL_SMALL
