import os

from dotenv import find_dotenv, load_dotenv
from agents import (Agent, Runner)


_ = load_dotenv(find_dotenv())

_ = load_dotenv(find_dotenv())

def _set_env(var: str, value: str):
    if not os.environ.get(var):
        os.environ[var] = value

# don't know why I must do this in debug mode
#_set_env("OPENAI_API_KEY", "openai")


agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.