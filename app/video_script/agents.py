from dataclasses import dataclass
from typing import Optional, TypedDict, List, Literal, Callable, Any

from ai_agents.base import Agent, Input, Output
from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSerializable
from langchain_core.runnables import RunnableConfig

from ai_agents import AbstractAgent

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
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name = name, model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Planner Agent")
        producer_prompt = hub.pull("video-script-producer-prompt")

        return producer_prompt | self.model.with_structured_output(Planning)
    

class Planning(TypedDict):
    video_title: str
    plan: List[Chapter]


#######################
# AGENT SDK EXAMPLE  #
#######################

from agents import (ItemHelpers, Runner as AgentSDKRunner, Agent as AgentSDKAgent, TResponseInputItem, gen_trace_id, trace)


class EvaluationFeedback(TypedDict):
    feedback: str
    score: Literal['pass', 'needs_improvement', 'fail']

    

class Planner2(Agent):
    def __init__(self, name: str, model_name: str):
        super().__init__(name = name)

        self.model_name = model_name    

        self.story_outline_generator = AgentSDKAgent(
            name="story_outline_generator",
            instructions=(
                "Créez un plan de script vidéo Youtube concis et engageant en suivant cette structure :\n\n"
            ),  
            model=self.model_name,
            output_type=Planning
        )

        self.evaluator = AgentSDKAgent(
            name="evaluator",
            instructions=(
                "Vous évaluez un plan de script vidéo Youtube selon ces critères spécifiques :\n"
            ),
            model=self.model_name,
            output_type=EvaluationFeedback
        )

    async def ainvoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        print("########################")
        print(input)
        print("########################")
        input_items: list[TResponseInputItem] = [{"content": input, "role": "user"}]

        latest_outline: Planning | None = None
        trace_id = gen_trace_id()
        # We'll run the entire workflow in a single trace
        with trace("Agent SDK Planner", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/{trace_id}")
            while True:
                story_outline_result = await AgentSDKRunner.run(
                    self.story_outline_generator,
                    input_items,
                )

                input_items = story_outline_result.to_input_list()
                latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)
                print("Story outline generated")

                evaluator_result = await AgentSDKRunner.run(
                    self.evaluator,
                    input_items,
                )       

                result: EvaluationFeedback = evaluator_result.final_output
                print(f"Evaluator score: {result.score}")

                if result.score == "pass":
                    print("Story outline is good enough, exiting.")
                    break

                print("Re-running with feedback")
                
                input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

        return Output(latest_outline)
    
    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
            input_items: list[TResponseInputItem] = [{"content": input, "role": "user"}]

            latest_outline: Planning | None = None

            # We'll run the entire workflow in a single trace
            with trace("Agent SDK Planner"):
                while True:
                    story_outline_result = AgentSDKRunner.run(
                        self.story_outline_generator,
                        input_items,
                    )

                    input_items = story_outline_result.to_input_list()
                    # latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)
                    latest_outline = story_outline_result.final_output
                    print("Story outline generated")

                    evaluator_result = AgentSDKRunner.run(self.evaluator, input_items)
                    result: EvaluationFeedback = evaluator_result.final_output

                    print(f"Evaluator score: {result.score}")

                    if result.score == "pass":
                        print("Story outline is good enough, exiting.")
                        break

                    print("Re-running with feedback")

                    input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

            print(f"Final story outline: {latest_outline}")
            return latest_outline


class Approval(TypedDict):
    status: Literal['approved', 'revised']

class Supervisor(AbstractAgent):
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name=name, model=model)
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
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name=name, model=model)
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
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name=name, model=model)
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
    def __init__(self, name: str, model: BaseChatModel):
        super().__init__(name=name, model=model)
        super().set_runnable(self._initiate_runnable())

    def _initiate_runnable(self) -> RunnableSerializable:
        logger.debug("Initiating Reviewer Agent")
        review_prompt = hub.pull("video-script-reviewer-prompt")
        return review_prompt | self.model.with_structured_output(ReviewFeedback)
