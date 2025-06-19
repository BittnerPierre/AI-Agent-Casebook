#!/usr/bin/env python3
"""
Test LangSmith tracing with global setup
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment FIRST
load_dotenv(find_dotenv())

# Set up global LangSmith tracing BEFORE importing agents
print("🔧 Setting up GLOBAL LangSmith tracing...")
from agents import set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor

# Set global trace processor
set_trace_processors([OpenAIAgentsTracingProcessor()])
print(f"✅ Global LangSmith tracing configured for project: {os.getenv('LANGSMITH_PROJECT')}")

# Now import and use agents
from agents import Agent, Runner

async def test_global_tracing():
    """Test agent with global tracing setup"""
    
    print("\n🤖 Testing with global trace processor setup...")
    
    agent = Agent(
        name="Global Trace Test Agent",
        instructions="You are a test agent. Always mention that you are being traced in LangSmith.",
        model="gpt-4o-mini"
    )
    
    print("🎯 Running agent with global tracing...")
    result = await Runner.run(
        starting_agent=agent,
        input="Hello! Please confirm you are being traced and tell me the current time."
    )
    
    print(f"📝 Agent response: {result.final_output}")
    print(f"🌐 Check LangSmith project: {os.getenv('LANGSMITH_PROJECT')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_global_tracing())