# AI Agent Casebook

This project aims to showcase "real-life" AI Multi-Agents systems.

## Introduction

We have two workflows for now:

- Customer Onboarding Assistant
- Video Script Assistant

We leverage mainly on [LangGraph](https://github.com/langchain-ai/langgraph) from LangChain for agentic workflows but we won't restrict to this.
Planner of video script assistant use [OpenAI's Agents SDK](https://openai.github.io/openai-agents-python/).

[CrewAI](https://www.crewai.com/open-source), and [PydanticAI](https://ai.pydantic.dev/) are also on the radar.

For LLM provider, we target Mistral AI (mistral-small) but also test against OpenAI GPT (gpt-4o-mini) and sometimes Anthropic Claude.

For Retrieval Augmental Generation, we use [ChromaDB](https://github.com/chroma-core/chroma) as Vector Store.

## Roadmap

- Common
- Advanced RAG (on-going)
- Customer Onboarding
- Strengthen Eligibility control
- Back-End: Streaming Event
- Query Augmentation
- Video Script
- Finalize workflow
- Research <-> Brainstorm
- Final revision

## Installation

1. Clone the Repository

```shell
git clone https://github.com/BittnerPierre/AI-Agent-Casebook
cd AI-Agent-Casebook
```

2. Configure Environment Variables

Create a .env file in the root directory and add your Mistral or OpenAI key.

```shell
echo "MISTRAL_API_KEY=your-api-key-here" > .env
```

We use LangChain hub to store prompt template. Langchain / Langsmith is free for individual developer.

```shell
echo "LANGCHAIN_API_KEY=your-api-key-here" > .env
```

## Installation

The project uses poetry for package management and has been tested with python 3.12.xx.

Main dependencies:

- Common
  - LangChain
  - LangGraph
  - MistralAI
  - Langsmith
  - pytests
- Script Editor
  - LlamaIndex (for RAG)
  - Tavily (for Search)
- Customer Onboarding
  - OpenAI
  - Chroma
  - FastAPI
  - Unicorn
  - SQLite
  - Vercel

Project uses dotenv to load ACCESS TOKEN to LLM platform.
You'll need OpenAI, Mistral, Langsmith key in a .env file.

### Customer Onboarding Specifics

Data (vectorstore chromadb and sql sqlite) are loaded from 'data' directory. It contains fake data generated with AI assistant.
Location can be setup in app/config.ini and test/config.ini.

- tools dir contains python script generator for langsmith test suite.
- tests covered most agents and assistants. Some tests will fail to show that it is better to use advanced testing :)

#### Front-End

Front-end is available in a separate project: [AI-Agent-Casebook-UI](ttps://github.com/BittnerPierre/AI-Agent-Casebook-UI). The front-end is in typescript and use React/NodeJS.

#### Run

To launch the backend, go to app directory and run

```
$> poetry run langgraph dev
```

## Youtube Video Script Generator

I've made a tutorial with this agentic workflows.

Youtube video (in french) that show the development of the ai workflow (simplified version):

[![IMAGE ALT TEXT HERE](https://i.ytimg.com/vi/0KY-73mwCdQ/hqdefault.jpg)](https://www.youtube.com/live/0KY-73mwCdQ)

[Tutorial](https://bittnerpierre.github.io/AI-Agent-Casebook/tutorials/agentic-script-writer.html)

[Notebook](https://github.com/BittnerPierre/AI-Agent-Casebook/blob/main/tutorials/agentic-script-writer.ipynb)

The langgraph workflow.

![image](res/video_script_state_graph.png)

## Customer Onboarding Assistant

This project aims to showcase agentic framework on a Customer Onboarding Assistant.

Youtube video (in french) explaining the project:

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/_rctwY6sVFM/0.jpg)](http://www.youtube.com/watch?v=_rctwY6sVFM)

### Architecture

#### Assistant Architecture Functional

![image](res/Schema_Fonctionnel.png)

#### Assistant Architecture with LCEL and Structured React

![image](res/Schema_LCEL-React.png)

#### Assistant Architecture with LangGraph

![image](res/Schema_LangGraph.png)

#### LangGraph generated graph

![image](res/state_graph.png)

## Licence

Apache Licence

## Code

Some inspiration was taken from LangGraph example (https://github.com/langchain-ai/langgraph) demo on simulator for pytest.
and agent-service-toolkit (https://github.com/JoshuaC215/agent-service-toolkit/) for streaming graph to front.
