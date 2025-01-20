from typing import Any, TypedDict, Annotated

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableSerializable
from langchain_core.runnables.utils import Input, Output
from langgraph.graph import add_messages

import abc
from typing import Optional


class RunnableMixin:
    def __init__(self):
        self.runnable: Optional[Runnable] = None

    def invoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """Implementation for invoking the agent."""
        return self.runnable.invoke(input, config) if self.runnable else None


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class AbstractAgent(abc.ABC, RunnableMixin):

    def __init__(self, model: BaseChatModel):
        """
        Initialize the AbstractAgent.

        :param model_name: Type of the language model to use.
        """
        super().__init__()
        self.model = model


    @abc.abstractmethod
    def _initiate_agent_chain(self) -> RunnableSerializable:
        pass

    @property
    def _runnable(self) -> Optional[Runnable]:
        """Expose a property to get the chain if available."""
        return self.runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


