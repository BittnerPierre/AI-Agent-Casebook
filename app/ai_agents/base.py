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

class Agent(abc.ABC):
    """
    Basic Agent interface that defines the minimal methods an agent must implement.
    This interface only requires invoke methods without the need to
    implement _initiate_runnable.
    """
    def __init__(self, name: str):
        """
        Initialize the Agent.

        Args:
            name: Name of the agent.
        """
        self.name = name

    @abc.abstractmethod
    def invoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """
        Synchronously process the input and produce an output.

        Args:
            input: The input data to process
            config: Optional configuration for the runnable
            **kwargs: Additional keyword arguments

        Returns:
            The output produced by the agent
        """
        pass

    @abc.abstractmethod
    async def ainvoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """
        Asynchronously process the input and produce an output.

        Args:
            input: The input data to process
            config: Optional configuration for the runnable
            **kwargs: Additional keyword arguments

        Returns:
            The output produced by the agent
        """
        pass


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
        # Remove the potentially recursive case
        # elif hasattr(self, 'invoke') and callable(getattr(self, 'invoke')):
        #     return self
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
            # Provide a clearer error message
            raise NotImplementedError("No runnable has been set. Make sure to call set_runnable")


    async def ainvoke(
            self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> Output:
        """Implementation for invoking the agent."""
        runnable = self.get_runnable
        if runnable:
            if isinstance(runnable, (Runnable, RunnableSequence)):
                result = await runnable.ainvoke(input, config, **kwargs)
                return result
            elif callable(runnable):
                result = runnable(input, config, **kwargs)
                # Si le résultat est une coroutine, il faut l'attendre
                if hasattr(result, '__await__'):
                    result = await result
            else:
                raise NotImplementedError("No valid invoke method found")
        else:
            # Provide a clearer error message
            raise NotImplementedError("No runnable has been set. Make sure to call set_runnable")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list[AnyMessage], add_messages]


class AbstractAgent(RunnableMixin,Agent):

    def __init__(self, name: str, model: BaseChatModel):
        """
        Initialize the AbstractAgent.

        :param name: Name of the agent.
        :param model: The language model to use.
        """
        RunnableMixin.__init__(self)
        Agent.__init__(self, name)
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

    def __init__(self, name: str, model: BaseChatModel, tools:Sequence[Callable[..., Any]]):
        """
        Initialize the AbstractAgentWithTools.

        :param name: Name of the agent.
        :param model: The language model to use.
        :param tools: Sequence of callable tools available to the agent.
        """
        self.tools = tools
        super().__init__(name, model)
