from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.crag import CragAgentState
from app.crag import decide_to_generate, retrieve, grade_documents, generate, transform_query, web_search

workflow = StateGraph(CragAgentState)

# NODES
# workflow.add_node("agent", agent)
# tool_node = ToolNode(tools=tools)

# Researcher with tools

# retrieve = ToolNode([retriever_tool])
workflow.add_node("retrieve", retrieve)  # retrieval
# workflow.add_edge(START, "retrieve")
# Decide whether to retrieve

workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search_node", web_search)
# workflow.add_node("rewrite", rewrite)  # Re-writing the question


# # Edges taken after the `action` node is called.
# workflow.add_conditional_edges(
#     "retrieve",
#     # Assess agent decision
#     grade_documents,
# )
#
# workflow.add_node(
#     "generate", generate
# )  # Generating a response after we know the documents are relevant

# workflow.add_edge("retrieve", "researcher")

# EDGES
# workflow.add_edge(START, "agent")
# workflow.add_conditional_edges(
#     "agent",
#     # Assess agent decision
#     tools_condition,
#     {
#         # Translate the condition outputs to nodes in our graph
#         "tools": "retrieve",
#         END: END,
#     },
# )

workflow.add_edge(START, "retrieve")

workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.add_edge("generate", END)
# workflow.add_edge("rewrite", "agent")

corrective_rag_graph = workflow.compile()  # checkpointer=memory