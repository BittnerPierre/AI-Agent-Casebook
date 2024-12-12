import configparser
import json
import os
import uuid
from typing import Any, List

from fastapi import FastAPI
from customer_onboarding.assistants import create_customer_onboarding_assistant_as_react_graph, \
    create_customer_onboarding_assistant_as_graph, create_customer_onboarding_assistant_as_chain
from customer_onboarding.commons import SupportedModel

from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from utils.prompt import ClientMessage, convert_to_openai_messages
from utils.tools import get_current_weather
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage

import uvicorn

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

app = FastAPI()

_config = configparser.ConfigParser()
_config.read('config.ini')
_faq_directory = _config.get('FAQAgent', 'faq_directory')
_persist_directory = _config.get('FAQAgent', 'persist_directory')
_problem_directory = _config.get('ProblemSolverAgent', 'problem_directory')

graph = create_customer_onboarding_assistant_as_graph(model_name=SupportedModel.DEFAULT)

lcel = create_customer_onboarding_assistant_as_chain(model_name=SupportedModel.DEFAULT)


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


async def stream_text(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
    draft_tool_calls = []

    # llm = ChatOpenAI(
    #     api_key=os.environ.get("OPENAI_API_KEY"),
    #     model="gpt-4o",
    #     streaming=True,
    #     stream_usage=True
    # ).bind_tools(
    #     tools=[get_current_weather],
    #     tool_choice="auto"
    # )

    config = {"configurable": {"thread_id": uuid.uuid4()}}
   # graph.ainvoke(input={"messages": messages}, config=config)

    langchain_messages = convert_openai_messages_to_langchain(messages=messages)

    async for chunk in graph.astream(input={"messages": langchain_messages}, config=config, stream_mode="messages"):
        if hasattr(chunk, 'content') and chunk.content:
            yield '0:{text}\n'.format(text=json.dumps(chunk.content))
        elif hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs.get('tool_calls'):
            if len(draft_tool_calls) == 0:
                draft_tool_calls.append({
                    "id": chunk.tool_call_chunks[0].get('id'),
                    "name": chunk.tool_call_chunks[0].get('name'),
                    "arguments": chunk.tool_call_chunks[0].get('args')
                })
            else:
                draft_tool_calls[0]["arguments"] += chunk.tool_call_chunks[0].get('args')
        elif hasattr(chunk, 'response_metadata') and chunk.response_metadata.get('finish_reason'):
            if chunk.response_metadata.get('finish_reason') == "tool_calls":
                for tool_call in draft_tool_calls:
                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                        id=tool_call['id'],
                        name=tool_call['name'],
                        args=tool_call['arguments'])
                    tool_result = available_tools[tool_call['name']].invoke(input=json.loads(tool_call['arguments']))

                    yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                        id=tool_call['id'],
                        name=tool_call['name'],
                        args=tool_call['arguments'],
                        result=json.dumps(tool_result))
            else:
                yield '0:{text}\n'.format(text=json.dumps(chunk.content))
        elif hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
            usage = chunk.usage_metadata
            prompt_tokens = usage.get('input_tokens')
            completion_tokens = usage.get('output_tokens')

            yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
                reason="tool-calls" if len(
                    draft_tool_calls) > 0 else "stop",
                prompt=prompt_tokens,
                completion=completion_tokens
            )


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    # langchain_messages = convert_openai_messages_to_langchain(messages=messages)
    # response = StreamingResponse(stream_text(openai_messages, protocol))
    # response.headers['x-vercel-ai-data-stream'] = 'v1'
    response = graph.invoke(input={"messages": openai_messages}, config=config)
    return ClientMessage(role="ai", content=response["messages"][-1].content)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/assist")
async def assist(messages=dict[str, Any]):
    # TODO manage with user session
    config = {"configurable": {"thread_id": uuid.uuid4()}}
    return await graph.ainvoke(input={"messages": messages}, config=config)


@app.get("/onboard")
async def onboard(messages=dict[str, Any]):
    # TODO manage with user session
    config = {"configurable": {"session_id": uuid.uuid4()}}
    return await lcel.ainvoke(input={"messages": messages}, config=config)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)