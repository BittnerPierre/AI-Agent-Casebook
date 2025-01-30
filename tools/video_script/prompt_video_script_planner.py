from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import MessagesPlaceholder, PromptTemplate

_ = load_dotenv(find_dotenv())

planner_prompt = PromptTemplate.from_template(
    "Elaborate the plan of the video script. \n"
    "Define for each chapter:\n"
    " - An engaging chapter 'Title' (words count for chapter in format 'X words')\n"
    " - Covered topics (max 3 per chapter) along motivation.\n"
    " - Brief for the chapter explaining where you want to go.\n"
    "You provide information that guide your team to deliver the story you envision.\n"
    "\n\n"
    "The video plan must follow this structure :\n"
    "- 'Opening Section': contains video hook and introduction.\n"
    "- 'Main Section': 'Body' of the script where you develop the X chapters.\n"
    "- 'Closing Section': contains the CTA (call to action) and a brief conclusion.\n"
    "\n\n"
    "Opening and Closing section does not count as 'user chapters'. "
    "If user ask for 3 chapters, you must plan for 5 (1: Hook+Introduction, 2,3,4: user chapters, 5: CTA+Conclusion)"
    "\n\n"
    "Here’s a simple, four-step formula for structuring the body of your script:\n"
    "- Step 1: Think about the main idea, the audience and the message you want to deliver.\n"
    "- Step 2: Select key messages and write down video hook and introduction that presents the principal ideas, "
    "that you want to develop in an engaging way so you don’t overwhelm your audience.\n"
    "- Step 3: Elaborate chapter individually on each ideas using examples from the context.\n"
    "- Step 4. Include the final call to action. Tell your audience what to do next.\n"
    "\n\n"
    "When done define an engaging 'video title' and 'chapter title' that will set the expectation"
    " for the video, drive user through your story and create curiosity gap."
    "The 'plan' and 'video title' must be in the same language as the script.\n\n"
    "{storytelling_guidebook}"
)

hub.push(repo_full_name="video-script-planner-prompt", object=planner_prompt, new_repo_is_public=False)

