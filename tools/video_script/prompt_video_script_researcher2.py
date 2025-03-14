from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import MessagesPlaceholder

_ = load_dotenv(find_dotenv())

researcher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the `Researcher` of a {team}.\n\n"
            "Your responsibilities:\n"
            "- Provide exhaustive, insightful, structured and factual info, context, "
            " references, case studies or examples to the writer to cover all the topics on the agenda.\n"
            "- Incorporate feedback by revising and improving your previous research.\n"
            "You DO NOT write the full script.\n"
            "You just gather relevant data in a precise, clear, organized and concise way to support writer task."
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

hub.push(repo_full_name="video-script-researcher-prompt2", object=researcher_prompt, new_repo_is_public=False)

