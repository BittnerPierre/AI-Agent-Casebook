from langchain_core.documents import Document

from app.crag import retriever, rag_chain, retrieval_grader, question_rewriter, web_search_tool, CragAgentState


async def retrieve(state: CragAgentState):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    documents = await retriever.ainvoke(question)
    return {"documents": documents, "question": question}


async def generate(state: CragAgentState):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = await rag_chain.ainvoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}


async def grade_documents(state: CragAgentState):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

     # Vérifier si la liste de documents est vide
    if not documents:
        print("---NO DOCUMENTS TO GRADE - WEB SEARCH REQUIRED---")
        return {
            "documents": [], 
            "question": question, 
            "web_search": "Yes"
        }

    # Score each doc
    filtered_docs = []
    web_search = "No"
    for d in documents:
        score = await retrieval_grader.ainvoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search = "Yes"
            continue

        # Si tous les documents ont été filtrés, forcer web_search à "Yes"
    if not filtered_docs:
        print("---ALL DOCUMENTS FILTERED OUT - WEB SEARCH REQUIRED---")
        web_search = "Yes"

    return {"documents": filtered_docs, "question": question, "web_search": web_search}


async def transform_query(state: CragAgentState):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = await question_rewriter.ainvoke({"question": question})
    return {"documents": documents, "query": better_question[:400]}


async def web_search(state: CragAgentState):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---WEB SEARCH---")
    query = state["query"]
    documents = state["documents"]

    # Web search
    docs = await web_search_tool.ainvoke({"query": query})
    print(docs)
    
    # Extraire le contenu des résultats de recherche web avec les sources
    if docs and "results" in docs and docs["results"]:
        web_results_parts = []
        for result in docs["results"]:
            if result.get("content"):
                # Formater chaque résultat avec titre, URL et contenu
                source_info = f"[Source: {result.get('title', 'Sans titre')} - {result.get('url', 'URL non disponible')}]"
                content = f"{source_info}\n{result['content']}"
                web_results_parts.append(content)
        
        web_results = "\n\n---\n\n".join(web_results_parts)
    else:
        web_results = "Aucun résultat de recherche web trouvé."
    
    web_results = Document(page_content=web_results)
    documents.append(web_results)

    return {"documents": documents}


async def decide_to_generate(state: CragAgentState):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    print(state["question"])
    web_search = state["web_search"]
    print(state["documents"])

    if web_search == "Yes":
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"
