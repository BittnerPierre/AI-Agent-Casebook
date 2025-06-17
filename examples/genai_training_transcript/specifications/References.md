# References

Here is a set of articles, documentations, papers, projects, blog posts and code examples that we will use as references for future development.

### Articles

#### Model Selection Guide - 3A. Use Case: Long-Context RAG for Legal Q&A - OpenAI

OpenAI engineering has shared a cookbook that serves as a practical guide to selecting, prompting, and deploying the right OpenAI model (between GPT 4.1, o3, and o4-mini) for specific workloads. Use Case 3A "Long-Context RAG for Legal Q&A" demonstrated how to Build an agentic system to answer questions from complex legal documents.

https://cookbook.openai.com/examples/partners/model_selection_guide/model_selection_guide#3a-use-case-long-context-rag-for-legal-qa

#### How we build our multi-agent research system - Anthropic

Anthropic Engineering explains on its blog how their Research feature uses multiple Claude agents to explore complex topics more effectively. We share the engineering challenges and the lessons we learned from building this system.

https://www.anthropic.com/engineering/built-multi-agent-research-system

### Code Examples

#### Research Bot - Agents SDK - OpenAI

This is a simple example from OpenAI Agents SDK of a multi-agent research bot.

https://github.com/openai/openai-agents-python/tree/main/examples/research_bot

#### Plan-And-Execute Agents - LangGraph

This notebook shows how to create a "plan-and-execute" style agent. This is heavily inspired by the Plan-and-Solve paper as well as the Baby-AGI project.

https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/plan-and-execute/plan-and-execute.ipynb

### Documentations

#### Hierarchical Agent - LangGraph

When tasks become too complex for a single worker or the number of workers grows too large, a hierarchical approach can improve system efficiency. This involves distributing work across multiple layers of supervision by composing subgraphs and introducing mid-level supervisors beneath a top-level supervisor, enabling more scalable and organized coordination.

https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/

#### Reasoning without Observation - LangGraph

Example of Planner approaching with LangGraph based on ReWOO paper (see Papers)

https://langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/

### Papers

#### Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models

https://arxiv.org/abs/2305.04091

#### ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models

https://arxiv.org/abs/2305.18323

#### AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation

https://arxiv.org/abs/2308.08155

### Projects

#### ReWOO Agent (NVidia)

The ReWOO (Reasoning WithOut Observation) Agent is an advanced AI system that decouples reasoning from observations to improve efficiency in augmented language models. Based on the ReWOO paper, this agent separates the planning and execution phases to reduce token consumption and improve performance.

The ReWOO Agent’s implementation follows the paper’s methodology of decoupling reasoning from observations, which leads to more efficient tool usage and better performance in complex reasoning tasks.

https://docs.nvidia.com/aiqtoolkit/latest/workflows/about/rewoo-agent.html

#### Baby-AGI

BabyAGI is an experimental framework for a self-building autonomous agent. Earlier efforts to expand BabyAGI have made it clear that the optimal way to build a general autonomous agent is to build the simplest thing that can build itself.

Note: interesting for the Logging part.

BabyAGI implements a comprehensive logging system to track all function executions and their interactions. The logging mechanism ensures that every function call, including its inputs, outputs, execution time, and any errors, is recorded for monitoring and debugging purposes.

https://github.com/yoheinakajima/babyagi
