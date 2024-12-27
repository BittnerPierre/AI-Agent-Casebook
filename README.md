# Customer Onboarding Assistant
This project aims to showcase agentic framework on a Customer Onboarding Assistant.
You'll only find the backend here.

Youtube video (in french) explaining the project:

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/_rctwY6sVFM/0.jpg)](http://www.youtube.com/watch?v=_rctwY6sVFM)

# Architecture

## Assistant Architecture Functional
![image](res/Schema_Fonctionnel.png)

## Assistant Architecture with LCEL and Structured React
![image](res/Schema_LCEL-React.png)

## Assistant Architecture with LangGraph
![image](res/Schema_LangGraph.png)

## LangGraph generated graph
![image](res/state_graph.png)

## Installation
The project uses poetry for package management and has been tested with python 3.10.12. 

Main dependencies: 
- LangChain
- LangGraph
- OpenAI
- MistralAI
- Langsmith
- Chroma
- Vercel
- FastAPI
- Unicorn
- SQLite

Data (vectorstore chromadb and sql sqlite) are loaded from 'data' directory. It contains fake data generated with AI assistant.
Location can be setup in app/config.ini and test/config.ini. 


- tools dir contains python script generator for langsmith test suite.
- tests covered most agents and assistants. Some tests will fail to show that it is better to use advanced testing :)

Project uses dotenv to load ACCESS TOKEN
You need OpenAI, Mistral, Langsmith key in a .env file

For the front-end, I've used a slightly modified *AI SDK Python streaming*:
https://vercel.com/templates/next.js/ai-sdk-python-streaming
https://github.com/vercel-labs/ai-sdk-preview-python-streaming

## Run

To launch the backend, go to app directory and run
```
$> poetry shell
$> python main.py
```

## Licence
Apache Licence

## Code
Some inspiration was taken from LangGraph example (https://github.com/langchain-ai/langgraph) demo on simulator for pytest.
and agent-service-toolkit (https://github.com/JoshuaC215/agent-service-toolkit/) for streaming graph to front.
