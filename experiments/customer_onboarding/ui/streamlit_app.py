"""
This module implements a Streamlit UI for a multi-agent chat system.
It handles the web interface, chat display, and agent responses.
"""
import sys
import os
# Add root to path for Streamlit cloud deployment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


import streamlit as st

from ..my_agents.agents import create_agent
from .utils import (
    initialize_session_state,
    load_css,
    render_header,
    setup_sidebar,
    display_chat_history,
    handle_chat_interaction
)


def main() -> None:
    """Main function to run the Streamlit app."""
    # Set page config
    st.set_page_config(
        page_title="AI Bot Chat",
        page_icon="🤖",
        layout="wide",
    )
    
    # Load custom CSS
    load_css()
    
    # Load header 
    render_header()
    
    # Set up sidebar with LLM provider configuration
    setup_sidebar()
    
    # Main chat history
    initialize_session_state()
    display_chat_history()
    
    # Create the agent and manage chat with model passed as an argument
    model = st.session_state.get("model")
    agent = create_agent(model=model)
    handle_chat_interaction(agent)


if __name__ == "__main__":
    main()