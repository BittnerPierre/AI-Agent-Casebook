#!/usr/bin/env python3
"""
Test centralized LangSmith tracing setup
"""

import os
import sys
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

# Add src to path
sys.path.insert(0, 'src')

# Set up centralized tracing FIRST
from common.langsmith_setup import configure_langsmith_tracing

print("🔧 Setting up centralized LangSmith tracing...")
tracing_enabled = configure_langsmith_tracing()
print(f"✅ Centralized tracing configured: {tracing_enabled}")

# Now use agents
from agents import Agent, Runner

async def test_centralized_tracing():
    """Test agent with centralized tracing setup"""
    
    print(f"\n🤖 Testing with centralized tracing (enabled: {tracing_enabled})...")
    
    agent = Agent(
        name="Centralized Trace Test",
        instructions="You are a test agent using centralized LangSmith tracing. Mention this in your response.",
        model="gpt-4o-mini"
    )
    
    print("🎯 Running agent with centralized tracing...")
    result = await Runner.run(
        starting_agent=agent,
        input="Hello! Please confirm you're using centralized LangSmith tracing and tell me about it."
    )
    
    print(f"📝 Agent response: {result.final_output}")
    print(f"🌐 Check LangSmith project: {os.getenv('LANGSMITH_PROJECT')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_centralized_tracing())