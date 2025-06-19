# AI Agent Casebook

This project showcases real-world implementations of **AI multi-agent systems**, using agentic frameworks such as **LangGraph** and **OpenAI's Agents SDK**.

## 🔍 Overview

We currently demonstrate two end-to-end agent workflows:

- **Customer Onboarding Assistant**
- **Video Script Assistant**

The goal is to explore production-ready AI agent use cases, focusing on:

- Agent orchestration (LangGraph, OpenAI Agents SDK)
- Multi-provider LLM compatibility (Mistral, OpenAI, Anthropic)
- Retrieval-Augmented Generation (ChromaDB, LlamaIndex)
- Evaluation & Testing of agent behavior

Future additions may include [CrewAI](https://www.crewai.com/open-source) and [PydanticAI](https://ai.pydantic.dev/).

---

## Roadmap

### Core

- Shared agent tools and testing setup

### Customer Onboarding Assistant

- Initial implementation
- Improve eligibility controls
- Streaming with server-sent events (SSE)
- Data refactor & backend cleanup

### Video Script Assistant

- Initial version with LangGraph
- Refactor planner with OpenAI Agents SDK
- Research + Ideation agent loop
- Final script review & CoT improvements

### RAG & Evaluation (WIP)

- Query Augmentation strategies
- Advanced testing with LangSmith & synthetic data

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/BittnerPierre/AI-Agent-Casebook
cd AI-Agent-Casebook
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```dotenv
# Required LLM providers
MISTRAL_API_KEY=your-mistral-key
OPENAI_API_KEY=your-openai-key
LANGCHAIN_API_KEY=your-langchain-key
```

> ⚠️ We recommend using [LangSmith](https://smith.langchain.com/) to monitor workflows. It's free for individual developers.

### 3. Install dependencies

This project uses **Poetry** with Python `>=3.12`.

```bash
poetry install
```

To activate the virtual environment:

```bash
poetry shell
```

## 🔒 Security & Vulnerability Scanning

This project includes automated security scanning of dependencies to ensure a secure development environment.

### Vulnerability Audit

The project includes `poetry-audit-plugin` as a development dependency for security scanning:

```bash
# Scan for vulnerabilities in project dependencies
poetry audit
```

This command scans all project dependencies against the Python Packaging Advisory Database and reports any known security vulnerabilities.

### For Team Members

When you clone the project and run `poetry install`, the audit plugin will be automatically available. Run `poetry audit` regularly to ensure your dependencies remain secure.

### CI/CD Integration

Consider adding `poetry audit` to your CI/CD pipeline to catch vulnerabilities early:

```yaml
# Example GitHub Actions step
- name: Security Audit
  run: poetry audit
```

---

## 📂 Project Structure

```bash
AI-Agent-Casebook/
│
├── app/                  # Main app logic and LangGraph workflows
├── data/                 # Fake onboarding data (vectorstore, SQLite)
├── tests/                # Agent test coverage (unit + integration)
├── tools/                # LangSmith suite and evaluation helpers
├── tutorials/            # Notebooks & walk-throughs
└── res/                  # Images and workflow diagrams
```

---

## Video Script Generator

A complete tutorial (in French) is available:

🎥 [Watch the YouTube video](https://www.youtube.com/live/0KY-73mwCdQ)

📘 [Tutorial (HTML)](https://bittnerpierre.github.io/AI-Agent-Casebook/tutorials/agentic-script-writer.html)
📓 [Notebook](https://github.com/BittnerPierre/AI-Agent-Casebook/blob/main/tutorials/agentic-script-writer.ipynb)

State graph (LangGraph):

![LangGraph script state](res/video_script_state_graph.png)

---

## Customer Onboarding Assistant

Project to demonstrate onboarding automation using agentic workflows.

[Watch the YouTube video (French)](http://www.youtube.com/watch?v=_rctwY6sVFM)

### Architectures

- **Functional view**

  ![Functional](res/Schema_Fonctionnel.png)

- **LCEL + React-like output**

  ![LCEL](res/Schema_LCEL-React.png)

- **LangGraph agent loop**

  ![LangGraph](res/Schema_LangGraph.png)

- **Generated graph**

  ![Graph](res/state_graph.png)

### Testing

- Use `pytest` with coverage across workflows
- Some tests are expected to fail: they demonstrate edge cases or brittle logic under test

---

## Front-End (Separate Repo)

The front-end (React/TypeScript) is available here:
[AI-Agent-Casebook-UI](https://github.com/BittnerPierre/AI-Agent-Casebook-UI)

> Designed for deployment on **Vercel**, communicating with the backend via API.

---

## Run Locally

To run the agent workflows locally (development mode):

```bash
poetry run langgraph dev
```

---

## License

Distributed under the **Apache License 2.0**.

---

## Credits & Inspiration

- [LangGraph](https://github.com/langchain-ai/langgraph) example simulators (pytest-style workflows)
- [agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit/) for ideas on streaming graphs to the UI
