from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph

from app.video_script.assistant import video_script
from app.customer_onboarding.assistant import customer_onboarding

DEFAULT_ASSISTANT = "customer-onboarding"


@dataclass
class Assistant:
    description: str
    graph: CompiledStateGraph


assistants: dict[str, Assistant] = {
    "customer-onboarding": Assistant(description="A customer onboarding assistant.", graph=customer_onboarding),
    "video-script": Assistant(description="A video script assistant.", graph=video_script),
}


def get_assistant(assistant_id: str) -> CompiledStateGraph:
    return assistants[assistant_id].graph
