from typing import Any, TypedDict, Annotated, TypeVar, Union, List, Callable, Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableSequence
from langgraph.graph import add_messages

import abc
from typing import Optional


Input = TypeVar("Input", contravariant=True)

# Output type should implement __concat__, as eg str, list, dict do
Output = TypeVar("Output", covariant=True)

class RunnableMixin:

    def __init__(self):
        self._runnable: Optional[Union[Runnable, Any]] = None

    def set_runnable(self, runnable: Optional[Union[Runnable, Any]]):
        """Set the runnable attribute."""
        self._runnable = runnable

    @property
    def get_runnable(self) -> Optional[Union[Runnable, RunnableSequence, Any]]:
        """Expose a property to get the chain if available."""
        if isinstance(self._runnable, (Runnable, RunnableSequence)):
            return self._runnable
        elif hasattr(self, 'invoke') and callable(getattr(self, 'invoke')):
            return self
        else:
            return None

    def invoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """Implementation for invoking the agent."""
        runnable = self.get_runnable
        if runnable:
            if isinstance(runnable, (Runnable, RunnableSequence)):
                return runnable.invoke(input, config, **kwargs)
            elif callable(runnable):
                return runnable(input, config, **kwargs)
            else:
                raise NotImplementedError("No valid invoke method found")
        else:
            raise NotImplementedError("No valid invoke method found")


    def ainvoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """Implementation for invoking the agent."""
        runnable = self.get_runnable
        if runnable:
            if isinstance(runnable, (Runnable, RunnableSequence)):
                return runnable.ainvoke(input, config, **kwargs)
            elif callable(runnable):
                return runnable(input, config, **kwargs)
            else:
                raise NotImplementedError("No valid invoke method found")
        else:
            raise NotImplementedError("No valid invoke method found")




class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list[AnyMessage], add_messages]



class AbstractAgent(abc.ABC, RunnableMixin):

    def __init__(self, model: BaseChatModel):
        """
        Initialize the AbstractAgent.

        :param model_name: Type of the language model to use.
        """
        super().__init__()
        self.model = model
        self.set_runnable(self._initiate_runnable())

    def __call__(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        return self.invoke(input, config, **kwargs)


    @abc.abstractmethod
    def _initiate_runnable(self):
        """
        Abstract method to initiate the runnable.
        """
        pass


class AbstractAgentWithTools(AbstractAgent, abc.ABC):

    def __init__(self, model: BaseChatModel, tools:Sequence[Callable[..., Any]]):
        """
        Initialize the AbstractAgent.

        :param model_name: Type of the language model to use.
        """
        self.tools = tools
        super().__init__(model)
