
import asyncio

from langchain_core.messages import HumanMessage

from video_script.assistant import create_video_script_agent


# Example of running the flow (asynchronously).
async def main():  # Define an async function
    #
    # Usage Example
    #
    # In real usage, you'd pass user messages or stored conversation. For now, we just pass empty messages to start.
    #
    config = {"recursion_limit": 99,
              "configurable": {"thread_id": "1"}}

    video_script_app = create_video_script_agent()

    prompt = ("I'd like a 3-chapter video of 3 minutes of 450 words on 'AI Won't Take Your Jobs."
                    " Those Who Use AI Will!', please!")

    example_input = {
        "messages": [HumanMessage(
            content=prompt)],
        # "chapters": [],         # or we let the planning node define them
        # "current_chapter": 0,   # start at chapter 0
        "final_script": ""  # empty at the start
    }

    # Collect all steps from the astream generator and print each step
    steps = []
    async for step in video_script_app.astream(example_input, config=config, stream_mode="values"):
        steps.append(step)
        print(f"Step: {step}")

    # Access the last step
    last_step = steps[-1]

    print(f"Directive: '{prompt}'")

    # Print the last message of the last step
    last_message = last_step["messages"][-1]

    output = last_message.pretty_repr()
    print(f"Result: '{output}'")

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function
