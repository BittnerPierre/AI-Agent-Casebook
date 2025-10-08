"""
This module implements a Streamlit UI for a multi-agent chat system.
It handles the web interface, chat display, and agent responses.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import streamlit as st

from my_agents import create_agent
from ui.utils import (
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
    
    # Create the agent and manage chat
    agent = create_agent()
    handle_chat_interaction(agent)


if __name__ == "__main__":
    main()