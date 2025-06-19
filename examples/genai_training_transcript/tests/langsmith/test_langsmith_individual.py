#!/usr/bin/env python3
"""
Test LangSmith tracing at the individual agent level
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

from agents import Agent, Runner
from langsmith.wrappers import OpenAIAgentsTracingProcessor

async def test_individual_tracing():
    """Test agent with individual trace processor"""
    
    print("🔧 Setting up individual agent tracing...")
    
    # Create trace processor
    trace_processor = OpenAIAgentsTracingProcessor()
    
    agent = Agent(
        name="Individual Trace Agent",
        instructions="You are a helpful assistant. Answer questions briefly.",
        model="gpt-4o-mini"
    )
    
    print(f"🌟 LangSmith project: {os.getenv('LANGSMITH_PROJECT')}")
    print(f"🔑 API key configured: {'✅' if os.getenv('LANGSMITH_API_KEY') else '❌'}")
    
    print("\n🤖 Running agent with individual tracing...")
    result = await Runner.run(
        starting_agent=agent,
        input="Hello, can you tell me your name?",
        hooks=[trace_processor]  # Apply tracing at run level
    )
    
    print(f"🎯 Result: {result.final_output}")
    print("✅ Individual tracing test completed")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_individual_tracing())