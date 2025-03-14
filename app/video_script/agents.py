from typing import TypedDict, List, Literal, Callable, Any

from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSerializable

from agents import AbstractAgent
from agents.base import AbstractAgentWithTools
from core.base import SupportedModel
from core.commons import initiate_model
from core.logger import logger

##############
# PRODUCER   #
##############


class Chapter(TypedDict):
    title: str
    covered_topics: List[str]
    chapter_brief: str


class Planning(TypedDict):
    video_title: str
    plan: List[Chapter]


class Planner(AbstractAgent):
    def __init__(self, model: BaseChatModel):
        super().__init__(model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Planner Agent")
        producer_prompt = hub.pull("video-script-producer-prompt")

        return producer_prompt | self.model.with_structured_output(Planning)



class Approval(TypedDict):
    status: Literal['approved', 'revised']

class Supervisor(AbstractAgent):
    def __init__(self, model: BaseChatModel):
        super().__init__(model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Planner Agent")
        producer_prompt = hub.pull("video-script-producer-prompt")
        return producer_prompt | self.model.with_structured_output(Approval)


##############
# RESEARCHER #
##############


class ResearchChapter(TypedDict):
    research: str
    comment: str


class Researcher(AbstractAgent):
    def __init__(self, model: BaseChatModel):
        super().__init__(model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Researcher Agent")
        researcher_prompt = hub.pull("video-script-researcher-prompt2")
        return researcher_prompt | self.model


##############
# WRITER     #
##############

class DraftChapter(TypedDict):
    chapter: str
    comment: str

class Writer(AbstractAgent):
    def __init__(self, model: BaseChatModel):
        super().__init__(model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Writer Agent")
        writer_prompt = hub.pull("video-script-writer-prompt")
        return writer_prompt | self.model.with_structured_output(DraftChapter)

##############
# REVIEWER   #
##############

class ReviewFeedback(TypedDict):
    GoodPoints: str
    MissingOrNeedsResearch: str
    SuperfluousContent: str
    StyleRefinement: str
    NextNode: Literal['researcher', 'writer', 'approved']


class Reviewer(AbstractAgent):
    def __init__(self, model: BaseChatModel):
        super().__init__(model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Reviewer Agent")
        review_prompt = hub.pull("video-script-reviewer-prompt")
        return review_prompt | self.model.with_structured_output(ReviewFeedback)
