
import asyncio

from langchain_core.messages import HumanMessage

from video_script.assistant import create_video_script_agent

example_input = {
    "messages": [HumanMessage(
        content="I'd like a 3-chapter video of 3 minutes of 300 words on 'AI Won't Take Your Jobs."
                " Those Who Use AI Will!', please!")],
    "chapters": [],         # or we let the planning node define them
    "current_chapter": 0,   # start at chapter 0
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


    # try:
    #     # Generate the image bytes from the graph
    #     image_bytes = video_script_app.get_graph().draw_mermaid_png()
    #     print("#######")
    #     print(video_script_app.get_graph().draw_mermaid())
    #     print("#######")
    #
    #     # Specify the filename where you want to save the image
    #     image_filename = "video_script_state_graph.png"
    #
    #     # Write the image bytes to the file
    #     with open(image_filename, "wb") as image_file:
    #         image_file.write(image_bytes)
    #
    #     print(f"Graph image saved as {image_filename}")
    # except Exception as e:
    #     print("An error occurred while generating the image:", str(e))

    async for step in video_script_app.astream(example_input, config=config):
        print(step)
        print("----")

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run to execute the function
