from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv


_ = load_dotenv(find_dotenv())

prompt = ChatPromptTemplate.from_template("""
### **Evaluation Prompt for Research (AI as Judge)**  

You are an evaluator assessing the relevance and adequacy of research results based on a defined **story request** 
and a **proposed planning**. 

Your goal is to determine whether the provided research aligns with the requested topic and provides useful, structured, and relevant information.  

Here is the evaluation data:
[BEGIN DATA]  
************  
<Request>
{input}
</Request>
************  
<Research>
{response}
</Research>
************
[END DATA]  

#### **Evaluation Process**  
1. **Relevance to Request**  
   - Does the research directly address the requested chapter and its covered topics?  
   - Does it stay within the intended scope without deviating into unrelated areas?  

2. **Alignment with Proposed Planning**  
   - Does the research sufficiently cover the key points outlined in the planning?  
   - Are the topics appropriately developed to provide meaningful insights?  

3. **Usefulness & Informational Value**  
   - Is the research **clear, structured, and informative**?  
   - Does it provide **credible information** (facts, explanations, or sources where applicable)?  
   - Can the content be **directly used** for the requested video script without requiring excessive modifications?  

#### **Evaluation Criteria (Score 0-10)**  
- **8-10**: The research is highly relevant, well-structured, and directly usable for the script.  
- **6-8**: Mostly aligned but may lack minor details or refinement.  
- **4-6**: Partially aligned, missing key elements or requiring significant rework.  
- **2-4**: Misaligned with the request, lacks important aspects, or includes off-topic content.  
- **0-2**: Irrelevant or not useful for the intended purpose.  

#### **Response Format:**  
**Grade:** <ACCEPTABLE or UNACCEPTABLE>  
**Score:** <0-10>  
**Comment:** <Brief justification for the score, highlighting any gaps or misalignment>  
"""
                                          )

hub.push("video-script-researcher-evaluator", prompt, new_repo_is_public=False)