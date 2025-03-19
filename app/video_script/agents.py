from dataclasses import dataclass
from typing import Optional, TypedDict, List, Literal, Callable, Any

from ai_agents.base import Agent, Input, Output
from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSerializable
from langchain_core.runnables import RunnableConfig

from ai_agents import AbstractAgent
from agents import (ItemHelpers, Runner as AgentSDKRunner, Agent as AgentSDKAgent, TResponseInputItem, gen_trace_id, trace)
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




@dataclass
class EvaluationFeedback:
    feedback: str
    score: Literal["pass", "needs_improvement", "fail"]



class Planner2(Agent):
    def __init__(self, name: str, model_name: str):
        super().__init__(name = name)

        self.model_name = model_name

        self.story_outline_generator = AgentSDKAgent(
            name="story_outline_generator",
            instructions=(
                "Créez un plan de script vidéo Youtube concis et engageant en suivant cette structure :\n\n"
                "1. OUVERTURE (Hook+Introduction) [~50 mots] :\n"
                "- Hook captivant\n"
                "- Introduction claire du sujet principal\n\n"
                "2. DÉVELOPPEMENT [~100 mots par chapitre] :\n"
                "- 2-3 chapitres maximum \n"
                "- Pour chaque chapitre :\n"
                "  • Titre accrocheur\n"
                "  • Points clés à développer (max 3)\n"
                "  • Message principal\n\n"
                "3. CONCLUSION (CTA+Conclusion) [~50 mots] :\n"
                "- Message final mémorable\n"
                "- Call-to-action clair\n\n"
                "PRINCIPES CLÉS :\n"
                "- Opening and Closing section does not count as 'user chapters'.\n"
                "- If user ask for 3 chapters, you must plan for 5 (1: Hook+Introduction, 2,3,4: user chapters, 5: CTA+Conclusion).\n"
                "- Ouverture et Conclusion sont obligatoires.\n"
                "- Confirmer la promesse du titre dès les premières secondes pour éviter la déception et maximiser la rétention.\n"
                "- Structurer les idées avant d’écrire avec une liste claire des points clés à aborder pour assurer un contenu percutant.\n"
                "- Accrocher avec une intro contrastée en présentant une croyance commune puis en la remettant en question pour captiver l’audience.\n"
                "- Hiérarchiser les arguments pour maintenir l’attention, en plaçant le 2ᵉ meilleur point en premier, le meilleur en second, puis les suivants.\n"  
                "- Conclure sur une note mémorable en résumant la valeur clé de la vidéo et en intégrant un appel à l’action fluide.\n" 
            ),
            model=self.model_name,
            output_type=Planning
        )
        self.evaluator = AgentSDKAgent[None](
            name="evaluator",
            instructions=(
                "Vous évaluez un plan de script vidéo Youtube selon ces critères spécifiques :\n"
                "\n"
                "1. Structure :\n"
                "- Présence des 3 parties : ouverture (~50 mots), développement (2-3 chapitres), conclusion (~50 mots)\n"
                "- Cohérence narrative entre les sections\n"
                "\n"
                "2. Contenu :\n"
                "- Hook engageant et promesse claire dans l'ouverture\n"
                "- Chapitres avec titres accrocheurs et points clés pertinents (max 3 par chapitre)\n"
                "- Message final et call-to-action impactants\n"
                "\n"
                "Ne demandez PAS :\n"
                "- Des exemples détaillés\n"
                "- Des scénarios concrets\n"
                "- Des métriques ou études de cas\n"
                "- Des détails sur les visuels\n"
                "\n"
                "Le plan doit rester stratégique et conceptuel. Concentrez-vous sur la structure, "
                "la progression logique et l'engagement narratif."
            ),
            output_type=EvaluationFeedback,
            model=self.model_name
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
                # latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)
                latest_outline = story_outline_result.final_output
                print("Story outline generated")

                evaluator_result = await AgentSDKRunner.run(self.evaluator, input_items)
                result: EvaluationFeedback = evaluator_result.final_output

                print(f"Evaluator score: {result.score}")

                if result.score == "pass":
                    print("Story outline is good enough, exiting.")
                    break

                print("Re-running with feedback")

                input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

        print(f"Final story outline: {latest_outline}")
        return latest_outline


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
