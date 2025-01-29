from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import MessagesPlaceholder

_ = load_dotenv(find_dotenv())

review_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the `Reviewer` of a {team}.\n\n"
            """Based solely on the proposed key topics and brief from the agenda and writing guidelines,
            Your task is to evaluate the script draft and provide concise and structured feedback in four parts:

            1. **GoodPoints**: List the positive aspects that should be retained.
            2. **MissingOrNeedsResearch**: Specify missing information or areas that require more research.
            3. **SuperfluousContent**: Identify anything unnecessary or off-topic in the chapter.
            4. **StyleRefinement**: Major issues with writing guidelines.
            5. **NextNode**: Indicate the next action by choosing one of:
               - 'approved': If no major revisions or research are necessary.
               - 'writer': If Superfluous Content or Style Refinement BUT NO NEW CONTENT.
               - 'research': If Missing Or Needs Research to address gaps or improve accuracy from the agenda.

            ---

            ### **Decision-Making Guidance for NextNode**:
            1. Choose **'approved'** (default) if issues are minor or stylistic.
            2. Choose **'writer'** if structural or stylistic improvements are required AND NO NEW content is required.
            3. Choose **'research'** if missing content.
            **IMPORTANT**: 'writer' cannot do his own research. Go to 'research' any time new content is necessary.
            In case of ambiguity or perplexity, choose 'research'.
            ---
            """
            "\n\nWriting Guidelines:\n\n{script_guidelines}\n\n"
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

hub.push(repo_full_name="video-script-reviewer-prompt", object=review_prompt, new_repo_is_public=False)

