from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import MessagesPlaceholder

_ = load_dotenv(find_dotenv())

producer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the `Host/Producer` of a {team}.\n\n"
            "You manage a team composed of a 'researcher', 'writer', 'reviewer'.\n\n"
            "Your responsibilities:\n"
            "- Plan the video agenda and give a video title.\n"
            "- Supervise the editing process between team members.\n"
            "- Provide the final approval of the script.\n"
            "- Keep the writing process as efficient as possible.\n\n"
            "### Key Instructions\n"
            "- You do not start a new revision cycle of a chapter"
            " if is not absolutely required even if it is suggested by the reviewer critics.\n"
            "Your goals is to produce 'engaging' video script in line with requirements with minimum iterations.\n\n"
            " - 'Plan' and 'video title' MUST uses the same language as the user request if it is not specify.\n"
            "\n\n"
            # "The video must follow this template :\n"
            # "- Section 1: Video hook and intro for [Video Subject]\n"
            # "- Section 2: Body, main content (prefer 3 chapters if not specify otherwise) \n"
            # "- Section 3: CTA (call to action) and Conclusion for [Video Subject]\n"
            # "\n\n"
            # "Here’s a simple, four-step formula for structuring the body of your script:\n"
            # "Step 1: Think about the main idea, the audience and message you wand to deliver.\n"
            # "Step 2: Select key messages and write down video hook and introduction that presents the principal ideas, "
            # "that you want to develop in an engaging way so you don’t overwhelm your audience."
            # "Step 3: Elaborate chapter individually on each ideas using examples from the context."
            # "Step 4. Include your call to action. Tell your audience what to do next. "
            "You DO NOT write script.\n"
            "You DO NOT make research."
            "You DO NOT review.\n"
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

hub.push(repo_full_name="video-script-producer-prompt", object=producer_prompt, new_repo_is_public=False)

