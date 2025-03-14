import os

from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core import initiate_embeddings, SupportedModel
from crag import corrective_rag_graph


from dotenv import load_dotenv, find_dotenv

from semantic_search.core import VectorStoreManager
from semantic_search.factory import SemanticSearchFactory, SearchStrategyType

# Import key from .env
_ = load_dotenv(find_dotenv())

os.environ["USER_AGENT"] = "Agentic RAG"

team = "small video editing team for Youtube channels"

tools = []

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    print("---CALL AGENT---")
    messages = state.messages
    model = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo")
    model = model.bind_tools(tools)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# def researcher_node(state: VideoScriptState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
#     """
#     The Researcher provides factual data/ideas for the current chapter.
#     For demonstration, we just append a dummy 'AIMessage' with bullet points.
#     """
#     message_content = f"Provide research for the script."
#     human_message = HumanMessage(content=message_content, name="user")
#     messages = list(state.messages) + [human_message]
#
#     researcher_prompt = hub.pull("video-script-researcher-prompt")
#     model = initiate_model(SupportedModel.GPT_4_O)
#     model_with_tools = model.bind_tools(tools)
#     researcher = researcher_prompt | model_with_tools
#
#     res = researcher.invoke(input={"messages": messages, "team": team}, config=config)
#
#     response = cast(
#         AIMessage,
#         res
#     )
#
#     if state.is_last_step and response.tool_calls:
#         return {
#             "messages": [
#                 AIMessage(
#                     id=response.id,
#                     content="Sorry, I could not find an answer to your question in the specified number of steps.",
#                 )
#             ]
#         }
#
#     # Return the model's response as a list to be added to existing messages
#     return {"messages": [response]}


# def rewrite(state):
#     """
#     Transform the query to produce a better question.
#
#     Args:
#         state (messages): The current state
#
#     Returns:
#         dict: The updated state with re-phrased question
#     """
#
#     print("---TRANSFORM QUERY---")
#     messages = state.messages
#     question = messages[0].content
#
#     msg = [
#         HumanMessage(
#             content=f""" \n
#     Look at the input and try to reason about the underlying semantic intent / meaning. \n
#     Here is the initial question:
#     \n ------- \n
#     {question}
#     \n ------- \n
#     Formulate an improved question: """,
#         )
#     ]
#
#     # Grader
#     model = initiate_model(SupportedModel.GPT_4_O)
#     response = model.invoke(msg)
#     return {"messages": [response]}


### Edges


def main():  # Define an async function


    config = {"recursion_limit": 25,
              "configurable": {"thread_id": "1"}}

    urls = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
    ]

    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]

    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=100,
    #     chunk_overlap=20,
    #     length_function=len,
    #     is_separator_regex=False,
    # )
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )
    doc_splits = text_splitter.split_documents(docs_list)

    search = VectorStoreManager.get_strategy()

    search.add_documents(doc_splits)

    # prompt = ("I'd like a 3-chapter video of 3 minutes of 450 words on 'AI Won't Take Your Jobs."
    #                 " Those Who Use AI Will!', please!")
    #
    # example_input = {
    #     "messages": [HumanMessage(
    #         content=prompt)],
    # }
    #
    # # Collect all steps from the astream generator and print each step
    # steps = []
    # for step in graph.stream(example_input, config=config, stream_mode="values"):
    #     steps.append(step)
    #     print(f"Step: {step}")
    #
    # # Access the last step
    # last_step = steps[-1]
    #
    # print(f"Directive: '{prompt}'")
    #
    # # Print the last message of the last step
    # last_message = last_step["messages"][-1]
    #
    # output = last_message.pretty_repr()
    # print(f"Result: '{output}'")

    import pprint

    inputs = {
        "messages": [
            ("user", "What does Lilian Weng say about the types of agent memory?"),
        ]
    }
    inputs = {"question": "What are the types of agent memory?"}
    # What does Lilian Weng say about the types of agent memory?
    # Write a script on what does Lilian Weng said about the types of agent memory.
    for output in corrective_rag_graph.stream(inputs):
        for key, value in output.items():
            pprint.pprint(f"Output from node '{key}':")
            pprint.pprint("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
        pprint.pprint("\n---\n")


if __name__ == "__main__":
    main()  # Use asyncio.run to execute the function