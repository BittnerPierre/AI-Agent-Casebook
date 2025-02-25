
import json

from uuid import uuid4
from typing import List

from fastapi import FastAPI, APIRouter, Query
from langchain_core._api import LangChainBetaWarning
from langchain_core.runnables import RunnableConfig

from core.base import SupportedModel

from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from assistants.core import get_assistant

from utils.prompt import ClientMessage, convert_to_openai_messages
from utils.tools import get_current_weather
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage

import uvicorn

from dotenv import load_dotenv, find_dotenv
import logging
import warnings


warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger(__name__)

_ = load_dotenv(find_dotenv())

app = FastAPI()
router = APIRouter()

default_model = SupportedModel.DEFAULT

class Request(BaseModel):
    messages: List[ClientMessage]


available_tools = {
    "get_current_weather": get_current_weather,
}


def convert_openai_messages_to_langchain(messages: List[ChatCompletionMessageParam]) -> List[BaseMessage]:
    # Convert OpenAI messages to LangChain messages
    langchain_messages = []
    for msg in messages:
        if msg["role"] == "user":
            content = msg["content"][0]["text"] if isinstance(msg["content"], list) else msg["content"]
            langchain_messages.append(HumanMessage(content=content))
        elif msg["role"] == "assistant":
            # Handle assistant messages with tool calls
            if "tool_calls" in msg and msg["tool_calls"] is not None:
                content = msg.get("content", "")
                langchain_messages.append(AIMessage(
                    content=content,
                    additional_kwargs={"tool_calls": msg["tool_calls"]}
                ))
            else:
                content = msg["content"][0]["text"] if isinstance(msg["content"], list) else msg["content"]
                langchain_messages.append(AIMessage(content=content))
        elif msg["role"] == "tool":
            # Only add tool messages if they are responses to tool calls
            langchain_messages.append(ToolMessage(
                content=msg["content"],
                tool_call_id=msg["tool_call_id"],
                name=msg.get("name", "")  # Add tool name if available
            ))
        elif msg["role"] == "system":
            langchain_messages.append(SystemMessage(content=msg["content"]))

    return langchain_messages


async def stream_text_graph(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
    run_id = uuid4()
    kwargs = {
        "input": {"messages": messages},
        "config": RunnableConfig(
            configurable={"thread_id": uuid4()}, run_id=run_id
        ),
    }

    graph = get_assistant("customer-onboarding")
    draft_tool_calls = []
    async for event in graph.astream_events(**kwargs, version="v2"):
        if not event:
            continue
        print(event)
        event_type = event["event"]
        tags = event.get("tags", [])
        # filter on the custom tag
        if event_type == "on_chain_stream" and "customer-onboarding" in event.get("name", []):
            data = event["data"]
            if 'messages' in data["chunk"]:
                chunk = data["chunk"]
                for message in chunk['messages']:
                    if message.content:
                        # yield '0:{text}\n'.format(text=json.dumps(message.content))
                        # TODO need to handle all cases. for now just streaming text
                        if hasattr(message, 'content') and message.content:
                            yield '0:{text}\n'.format(text=json.dumps(message.content))
                        elif hasattr(message, 'additional_kwargs') and message.additional_kwargs.get('tool_calls'):
                            if len(draft_tool_calls) == 0:
                                draft_tool_calls.append({
                                    "id": message.tool_call_chunks[0].get('id'),
                                    "name": message.tool_call_chunks[0].get('name'),
                                    "arguments": message.tool_call_chunks[0].get('args')
                                })
                            else:
                                draft_tool_calls[0]["arguments"] += message.tool_call_chunks[0].get('args')
                        elif hasattr(message, 'response_metadata') and message.response_metadata.get('finish_reason'):
                            if message.response_metadata.get('finish_reason') == "tool_calls":
                                for tool_call in draft_tool_calls:
                                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                                        id=tool_call['id'],
                                        name=tool_call['name'],
                                        args=tool_call['arguments'])
                                    tool_result = available_tools[tool_call['name']].invoke(
                                        input=json.loads(tool_call['arguments']))

                                    yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                                        id=tool_call['id'],
                                        name=tool_call['name'],
                                        args=tool_call['arguments'],
                                        result=json.dumps(tool_result))
                            else:
                                yield '0:{text}\n'.format(text=json.dumps(message.content))
                        elif hasattr(message, 'usage_metadata') and message.usage_metadata:
                            usage = message.usage_metadata
                            prompt_tokens = usage.get('input_tokens')
                            completion_tokens = usage.get('output_tokens')

                            yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
                                reason="tool-calls" if len(
                                    draft_tool_calls) > 0 else "stop",
                                prompt=prompt_tokens,
                                completion=completion_tokens
                            )


@router.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)
    response = StreamingResponse(stream_text_graph(openai_messages, protocol))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)