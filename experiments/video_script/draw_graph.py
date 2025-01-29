
import asyncio

from langchain_core.messages import HumanMessage

from video_script.assistant import create_video_script_agent

def main():  # Define an async function

    video_script_app = create_video_script_agent()

    try:
        # Generate the image bytes from the graph
        image_bytes = video_script_app.get_graph().draw_mermaid_png()
        print("#######")
        print(video_script_app.get_graph().draw_mermaid())
        print("#######")

        # Specify the filename where you want to save the image
        image_filename = "video_script_state_graph.png"

        # Write the image bytes to the file
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)

        print(f"Graph image saved as {image_filename}")
    except Exception as e:
        print("An error occurred while generating the image:", str(e))

if __name__ == "__main__":
    main()
