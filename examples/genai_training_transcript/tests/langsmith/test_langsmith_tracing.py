#!/usr/bin/env python3
"""
Simple test to verify LangSmith tracing with OpenAI Agents SDK is working
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

# Set up LangSmith tracing
from agents import Agent, Runner, set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor

print("🔧 Setting up LangSmith tracing...")
set_trace_processors([OpenAIAgentsTracingProcessor()])
print(f"✅ LangSmith tracing configured for project: {os.getenv('LANGSMITH_PROJECT')}")

async def test_simple_agent():
    """Test simple agent with LangSmith tracing"""
    
    agent = Agent(
        name="Simple Test Agent",
        instructions="You are a helpful assistant. Answer questions briefly.",
        model="gpt-4o-mini"
    )
    
    print("\n🤖 Running simple agent test...")
    result = await Runner.run(
        starting_agent=agent,
        input="What is 2+2? Just give me the number."
    )
    
    print(f"🎯 Result: {result.final_output}")
    print("✅ Test completed - check LangSmith dashboard for traces")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_simple_agent())