
import asyncio

from langchain_core.messages import HumanMessage

from video_script.assistant import create_video_script_agent

example_input = {
    "messages": [HumanMessage(
        content="I'd like a 2-chapter video of 3 minutes of 450 words on 'AI Won't Take Your Jobs."
                " Those Who Use AI Will!', please!")],
    # "chapters": [],         # or we let the planning node define them
    # "current_chapter": 0,   # start at chapter 0
    "final_script": ""      # empty at the start
}

# Example of running the flow (asynchronously).


async def main():  # Define an async function
    #
    # Usage Example
    #
    # In real usage, you'd pass user messages or stored conversation. For now, we just pass empty messages to start.
    #
    config = {"recursion_limit": 40,
              "configurable": {"thread_id": "1"}}

    video_script_app = create_video_script_agent()

    # val = await video_script_app.ainvoke(input=example_input, config=config, stream_mode="values")
    #
    # print(val)
    #
    # async for step in video_script_app.astream(example_input, config=config):
    #     print(step)
    #     print("----")

    # Collect all steps from the astream generator
    steps = [step async for step in video_script_app.astream(example_input, config=config, stream_mode="values")]

    # Access the last step
    last_step = steps[-1]

    # Print the last step
    # print(last_step)

    # Print the last message of the last step
    last_message = last_step["messages"][-1]
    last_message.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function
