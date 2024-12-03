from langchain import hub
from langchain.prompts.chat import ChatPromptTemplate

from dotenv import find_dotenv, load_dotenv


_ = load_dotenv(find_dotenv())

prompt = ChatPromptTemplate.from_template("""
    You are comparing a submitted answer to an expert answer on a given question. Here is the data:
    [BEGIN DATA]
    ************
    [Question]: {query}
    ************
    [Expert]: {answer}
    ************
    [Submission]: {result}
    ************
    [END DATA]

    Compare the factual content of the submitted answer with the expert answer.
    Ignore any differences in style, grammar, or punctuation.
    
    The submitted answer may either be a subset or superset of the expert answer, or it may conflict with it.
    Determine which case applies. 
    
    Answer the question grading the result :
    Between 8 to 10 : The submitted answer is a subset of the expert answer and is fully consistent with it.
    Between 6 to 8 : The submitted answer is a superset of the expert answer and is fully consistent with it.
    Between 4 to 6 : The submitted answer contains all the same details as the expert answer.
    Between 2 to 4 : There is a disagreement between the submitted answer and the expert answer.
    Between 0 to 2 : The answers differ, but these differences don't matter from the perspective of factuality.
    
    The answer is CORRECT if the score is above 6. It is INCORRECT if the score is below 6.
    
    Answer in the following format:
    Grade: <CORRECT or INCORRECT>
    Score: <grade frome 0 to 10>
"""
                                          )

hub.push("customer-onboarding-evaluator", prompt, new_repo_is_public=False)