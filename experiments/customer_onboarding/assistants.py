import sys

from langchain_core.messages import HumanMessage, AIMessage

from core.base import SupportedModel
from customer_onboarding.assistants import create_customer_onboarding_assistant_as_graph


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()




if __name__ == "__main__":
    print(sys.path)

    # TODO TO REMOVE THIS IS TESTING

    graph = create_customer_onboarding_assistant_as_graph(model_name=SupportedModel.DEFAULT)

    # try:
    #     # Generate the image bytes from the graph
    #     image_bytes = graph.get_graph().draw_mermaid_png()
    #     print("#######")
    #     print(graph.get_graph().draw_mermaid())
    #     print("#######")
    #
    #     # Specify the filename where you want to save the image
    #     image_filename = "../state_graph.png"
    #
    #     # Write the image bytes to the file
    #     with open(image_filename, "wb") as image_file:
    #         image_file.write(image_bytes)
    #
    #     print(f"Graph image saved as {image_filename}")
    # except Exception as e:
    #     print("An error occurred while generating the image:", str(e))


    chat_history = [
        HumanMessage(content="Je veux ouvrir un compte."),
        AIMessage(content="Où résidez-vous actuellement ?"),
        HumanMessage(content="Je réside en France."),
        AIMessage(content="Êtes-vous de nationalité française ?"),
        HumanMessage(content="Oui, je suis Français. J'ai 24 ans."),
        AIMessage(content="Possédez-vous un compte bancaire en France ?"),
        HumanMessage(content="Oui.")
    ]

    inputs = {"messages": chat_history}
    config = {"configurable": {"thread_id": "13579"}}
    print_stream(graph.stream(inputs, config=config,  stream_mode="values"))
    #
    # inputs = {"messages": [("user", "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?")]}
    # config = {"configurable": {"thread_id": "1"}}
    # print_stream(graph.stream(inputs, config=config, stream_mode="values"))
    #
    # inputs = {"messages": [("user", "Je ne reçois pas l'e-mail pour valider mon compte.")]}
    # config = {"configurable": {"thread_id": "1"}}
    # print_stream(graph.stream(inputs, config=config, stream_mode="values"))

    inputs = {"messages": [HumanMessage(content="Je ne reçois pas l'e-mail pour valider mon compte.")]}
    config = {"configurable": {"thread_id": "2"}}
    print_stream(graph.stream(inputs, config=config, stream_mode="values"))

    # assistant = create_customer_onboarding_assistant(model_name=SupportedModel.DEFAULT,
    #                                                  faq_directory=_faq_directory,
    #                                                  problem_directory=_problem_directory,
    #                                                  persist_directory=_persist_directory)
    #
    # chat_history = [
    #     HumanMessage(content="Je veux ouvrir un compte."),
    #     AIMessage(content="Question: Où résidez-vous actuellement ?"),
    #     HumanMessage(content="Je réside en France."),
    #     AIMessage(content="Question:Êtes-vous de nationalité française ?"),
    #     HumanMessage(content="Oui, je suis Français."),
    #     AIMessage(content="Question: Possédez-vous un compte bancaire en France ?"),
    # ]
    #
    # session_id = '12345'
    # # message_history = get_message_history(session_id)
    # # # message_history.add_messages(chat_history)
    # #
    # # # human_msg1 = "Oui, j'ai un compte bancaire en France."
    # human_msg1 = "Je veux ouvrir un compte."
    # ai_msg_1 = assistant.invoke(input={'input': human_msg1, 'user_session_id': session_id},
    #                                                 config={'configurable': {'session_id': session_id}})
    # print(ai_msg_1)

