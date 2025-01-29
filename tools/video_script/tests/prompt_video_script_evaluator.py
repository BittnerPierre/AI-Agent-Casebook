from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv


_ = load_dotenv(find_dotenv())

prompt = ChatPromptTemplate.from_template("""
You are evaluating a submitted script based on the given request. 

Here is the evaluation data:
[BEGIN DATA]  
************  
<Request>
{input}
</Request>
************  
<SubmittedScript>
{response}
</SubmittedScript>
************
[END DATA]  

Compare the submitted script with the request.  
Ignore differences in style, minor phrasing, or wording variations.  

Assess alignment based on:  
- **Structure**: Does it follow a logical **chapitrage** (proposed agenda)?  
- **Angle**: Does the story perspective fit the topic?  
- **Length & Duration**: Is it reasonably aligned with expectations?  
- **Language**: Does the script is in the expected language (same as request if user not specify)?  
- **Quality**: Is it coherent, engaging, and suitable for a YouTube AI audience?  

**Grade the result:**  
- **8 to 10**: Fully meets the request across all aspects.  
- **6 to 8**: Mostly aligned, with minor gaps.  
- **4 to 6**: Partially aligned, missing key aspects.  
- **2 to 4**: Significant misalignment with the request.  
- **0 to 2**: Off-topic or completely missing expectations.  
If the submission is entirely missing or contains no meaningful content (ex: None), assign a score of 0.
The script is **ACCEPTABLE** if the score is above 6. It is **UNACCEPTABLE** if the score is below 6.  

**Answer format:**  
Grade: <ACCEPTABLE or UNACCEPTABLE>  
Score: <grade from 0 to 10>"**  
"""
                                          )

hub.push("video-script-evaluator", prompt, new_repo_is_public=False)