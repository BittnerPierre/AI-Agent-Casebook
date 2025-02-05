from typing import TypedDict, Literal

import pytest
from langchain import hub
from langchain_core.messages import HumanMessage, AIMessage

from core.commons import initiate_model
from core.base import SupportedModel
from video_script.agents import Researcher

default_model = SupportedModel.DEFAULT

TESTING = False

# FOR TESTING THE TEST :)
TEST_SCRIPT_FILENAME = "tests/video_script/test_researcher.json"

team = "small video editing team for Youtube channels"


def load_test_script(logger):
    try:
        with open(TEST_SCRIPT_FILENAME, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"No guidelines available {TEST_SCRIPT_FILENAME}.")
        return "No script guidelines available."


class ScriptEvaluatorFeedback(TypedDict):
    Grade: Literal['ACCEPTABLE', 'UNACCEPTABLE']
    Score: int
    Comment: str


eval_llm = initiate_model(default_model)

evaluator_prompt = hub.pull("video-script-researcher-evaluator")

script_evaluator = evaluator_prompt | eval_llm.with_structured_output(ScriptEvaluatorFeedback)


@pytest.fixture
def model():
    return initiate_model(default_model)


@pytest.fixture
def agent(model):
    researcher = Researcher(model=model)
    return researcher


def valid_script(input: str, output: str) -> ScriptEvaluatorFeedback:
  """Use an LLM to judge if the script is consistent."""

  res = script_evaluator.invoke(input={"input": input, "response": output})
  return res


async def test_researcher(config, logger, agent):
    logger.info(f"test_researcher START (test_mode={TESTING})")

    # TODO I THINK I COULD MOVE THIS IN LANGSMITH
    input = [
        HumanMessage(content=("Je voudrais une vidéo en deux chapitres d'une durée de 2 minutes et contenant 450 mots sur le sujet "
             "`L'IA ne prendra pas votre travail. Ceux qui utilisent l'IA, oui !`, s'il vous plaît !")),
        AIMessage(name="host-producer", content="""Here's a suggested agenda for your 2-chapter video on L'IA et l'avenir du travail :
                        Comment les compétences en IA peuvent booster votre carrière.

                       L'IA ne prendra pas votre travail. Ceux qui utilisent l'IA le feront ! (200 mots):
                         - Brief: Introduction de la vidéo, présentation du sujet et des points principaux qui seront abordés.
                         - Covered Topics:
                           - Comprendre le rôle de l'IA dans le monde du travail
                           - Les avantages de l'IA pour les travailleurs
                           - Les compétences nécessaires pour travailler avec l'IA

                       L'IA et les opportunités de carrière (250 mots):
                         - Brief: Présentation des entreprises qui réussissent grâce à l'IA, des compétences recherchées et des opportunités de carrière.
                         - Covered Topics:
                           - Les entreprises qui ont réussi grâce à l'IA
                           - Les compétences recherchées par les entreprises
                           - Les opportunités de carrière avec l'IA"""),
        HumanMessage(name="user", content="Provide research for the chapter 'L'IA ne prendra pas votre travail."
                                          " Ceux qui utilisent l'IA le feront ! (200 mots)' covering the key topics."),
    ]

    if TESTING:
        output = load_test_script(logger)
    else:
        output = await agent.ainvoke(input={"messages": input, "team": team})

    res = valid_script(input, output)

    logger.info(f"test_researcher END {res} (test_mode={TESTING})")
    assert res["Grade"], "Acceptable"
