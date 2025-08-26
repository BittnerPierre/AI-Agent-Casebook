from dataclasses import dataclass
from typing import Optional, TypedDict, List, Literal, Callable, Any

from app.ai_agents.base import Agent, Input, Output
from langchain import hub
from langsmith import AsyncClient
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSerializable
from langchain_core.runnables import RunnableConfig

from app.ai_agents import AbstractAgent

from app.core.logger import logger

import json


# Créer un client asynchrone LangSmith
async_client = AsyncClient()

##############
# PRODUCER   #
##############


class Chapter(TypedDict):
    title: str
    covered_topics: List[str]
    chapter_brief: str
    sources: Optional[List[str]]


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


EVALUATOR_INSTRUCTIONS = """
You are an expert evaluator of YouTube script outlines.  
Your job is to decide whether the proposed outline matches the USER PROMPT and if the workflow should continue.  

Start with a short internal checklist (3–7 steps) to guide your evaluation before analyzing.  

EVALUATION RULES

1. Subject & Relevance
- The outline must match the requested topic.  
- Off-topic outline => FAIL.  

2. Structure (Chapters)
- The number of **content chapters** must match exactly what the USER PROMPT requires.  
- ⚠️ Critical rule: If the USER PROMPT asks for 1 chapter and the outline has exactly 1 content chapter, this MUST be considered correct.  
- Intro/Hook and Conclusion/Call to Action must NEVER be counted as content chapters, even if labeled as “chapter”.  
- Do not infer that an intro or conclusion is mandatory. Their absence is acceptable as long as the number of content chapters matches the USER PROMPT.  
- If the plan is unstructured or in raw text, use judgment to identify and count only the main content chapters.  

3. Specific Constraints
- If the USER PROMPT explicitly requires examples, tools, or sources, they must appear (or be marked as “to be added by researcher”).  
- Expected style (e.g., conversational, simple, clear) should be reflected in briefs and covered topics.  
- Word count or duration are objectives for the writing stage: NEVER FAIL an outline for not including them at the planning stage.  

4. Minimum Quality
- Each content chapter must include a title, a brief summary, and specific/actionable covered topics.  
- The outline must follow a logical progression without major redundancy.  

DECISION
- FAIL ONLY IF:  
  (a) the outline is off-topic,  
  (b) the number of content chapters (after excluding intro/conclusion/CTA) does not match the USER PROMPT,  
  (c) explicit required sources are missing.  
- NEEDS_IMPROVEMENT if the outline matches the topic and chapter count but needs refinement (e.g., missing CTA, vague topics, missing word budget).  
- PASS if fully compliant.  

OUTPUT FORMAT (STRICT JSON only):  
```json
{
  "score": "pass" | "needs_improvement" | "fail",
  "feedback": "Concise and actionable explanation. If fail, start with 'FAIL_REASON: <reason>'. If needs_improvement, briefly list corrections required."
}
```
"""


class Planner2(Agent):
    def __init__(self, name: str, model_name: str):
        super().__init__(name = name)
        self.model_name = model_name    

        self.story_outline_generator = AgentSDKAgent(
            name="story_outline_generator",
            instructions=(
                """Developer: Begin with a concise checklist (3–7 bullets) outlining the steps you will take to create the YouTube video script outline. Strictly adhere to the USER PROMPT throughout. 

                    Rules:
                    - Always start with an Introduction (Hook) and end with a Conclusion (Call to Action).
                    - Do not count the Introduction and Conclusion as content chapters; only generate the number of content chapters explicitly requested.
                    • If only one chapter is requested: merge the Introduction and Conclusion into the single chapter’s brief.
                    • If multiple chapters are requested: format as Introduction + content chapters + Conclusion.
                    - For each content chapter:
                    • Provide a clear, descriptive chapter title.
                    • Include 2–4 precise 'covered_topics' as bullet points detailing what the chapter develops.
                    • Supply a concise, actionable 'chapter_brief' (2–4 sentences) as scriptwriter guidance.
                    • Add an optional 'sources' field: if the USER PROMPT provides explicit references, URLs, or documents, cite them here; otherwise, use placeholders if additional research is needed.
                    - When a duration or word count is specified in the USER PROMPT, insert a target directive in the brief (e.g., “Target ~150 words (~1 minute)”).
                    - Never infer or create any style, tone, length, or sources unless stated in the USER PROMPT. 
                    - After creating the outline, validate that all requirements are met and all fields are present, correcting any omissions or errors before returning the output."""
            ),
            model=self.model_name,
            output_type=Planning
        )

        self.evaluator = AgentSDKAgent(
            name="evaluator",
            instructions=EVALUATOR_INSTRUCTIONS,  # <-- utilise le prompt robuste ci-dessus
            model=self.model_name,
            output_type=EvaluationFeedback
        )

    def _format_plan_for_evaluation(self, plan: List[Chapter], video_title: Optional[str] = None) -> str:
        formatted = "Plan du script vidéo :\n\n"
        if video_title:
            formatted += f"Titre de la vidéo: {video_title}\n\n"
        for i, chapter in enumerate(plan, 1):
            title = chapter.get('title') or f"Chapitre {i}"
            topics = chapter.get('covered_topics') or []
            brief = chapter.get('chapter_brief') or ""
            formatted += f"Chapitre {i}: {title}\n"
            if topics:
                formatted += f"  Sujets couverts: {', '.join(topics)}\n"
            if brief:
                formatted += f"  Résumé: {brief}\n"
            # Si tu ajoutes un budget de mots par chapitre :
            if 'word_budget' in chapter:
                formatted += f"  Budget mots (~): {chapter['word_budget']}\n"
            formatted += "\n"
        return formatted


    def _build_evaluation_request(self, user_prompt: str, planning_obj: dict) -> str:
        # planning_obj est l'objet 'Planning' retourné par le planner (avec keys: video_title, plan: [...] )
        plan_json = json.dumps(planning_obj, ensure_ascii=False)
        return (
            "### USER PROMPT\n"
            f"{user_prompt.strip()}\n\n"
            "### PLAN JSON\n"
            f"{plan_json}\n\n"
            "### TÂCHE\n"
            "Évaluez le PLAN par rapport au USER PROMPT en appliquant STRICTEMENT les règles d’évaluation. "
        )

    async def ainvoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        # input == user prompt (exigences utilisateur)
        user_prompt_str = str(input)
        input_items: list[TResponseInputItem] = [{"content": user_prompt_str, "role": "user"}]

        latest_outline: Planning | None = None
        trace_id = gen_trace_id()
        with trace("Agent SDK Planner", trace_id=trace_id):
            while True:
                story_outline_result = await AgentSDKRunner.run(
                    self.story_outline_generator,
                    input_items,
                )

                latest_outline = story_outline_result.final_output  # Planning
                result: Planning = latest_outline

                formatted_plan = self._format_plan_for_evaluation(result['plan'], video_title=result.get('video_title'))
                planning_obj = latest_outline 
                eval_request = self._build_evaluation_request(user_prompt_str, planning_obj)

                # On envoie AU JUGE à la fois le user prompt et le plan
                evaluator_result = await AgentSDKRunner.run(
                    self.evaluator,
                    [{"content": eval_request, "role": "user"}],
                )

                eval_feedback: EvaluationFeedback = evaluator_result.final_output
                score = eval_feedback['score']

                if score == "pass":
                    break

                if score == "fail":
                    # Stoppe net pour économiser des tokens
                    # Tu peux aussi logger eval_feedback['feedback'] pour diagnostic
                    return Output({
                        "status": "stopped",
                        "reason": "fail",
                        "evaluation": eval_feedback,
                    })

                # needs_improvement -> on boucle en fournissant le feedback
                input_items = [
                    {"content": user_prompt_str, "role": "user"},
                    {"content": formatted_plan, "role": "user"},
                    {"content": f"Feedback: {eval_feedback['feedback']}", "role": "user"},
                ]

        return Output(latest_outline)

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        user_prompt_str = str(input)
        input_items: list[TResponseInputItem] = [{"content": user_prompt_str, "role": "user"}]
        latest_outline: Planning | None = None

        with trace("Agent SDK Planner"):
            while True:
                story_outline_result = AgentSDKRunner.run(
                    self.story_outline_generator,
                    input_items,
                )
                latest_outline = story_outline_result.final_output
                result: Planning = latest_outline

                formatted_plan = self._format_plan_for_evaluation(result['plan'])
                planning_obj = latest_outline 
                eval_request = self._build_evaluation_request(user_prompt_str, planning_obj)

                evaluator_result = AgentSDKRunner.run(
                    self.evaluator,
                    [{"content": eval_request, "role": "user"}],
                )
                eval_feedback: EvaluationFeedback = evaluator_result.final_output
                score = eval_feedback['score']

                if score == "pass":
                    break

                if score == "fail":
                    return Output({
                        "status": "stopped",
                        "reason": "fail",
                        "evaluation": eval_feedback,
                    })

                input_items = [
                    {"content": user_prompt_str, "role": "user"},
                    {"content": formatted_plan, "role": "user"},
                    {"content": f"Feedback: {eval_feedback['feedback']}", "role": "user"},
                ]

        return Output(latest_outline)



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
