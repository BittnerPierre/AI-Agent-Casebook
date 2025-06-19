#!/usr/bin/env python3
"""
Test LangSmith tracing with LANGSMITH_TRACING=true flag
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

# Set up LangSmith tracing with flag
from agents import Agent, Runner, set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor

async def test_with_tracing_flag():
    """Test agent with tracing flag enabled"""
    
    print("🔧 Environment check:")
    print(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING')}")
    print(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")
    print(f"LANGSMITH_API_KEY: {'✅ Set' if os.getenv('LANGSMITH_API_KEY') else '❌ Missing'}")
    
    # Configure tracing
    if os.getenv('LANGSMITH_TRACING', '').lower() == 'true':
        print("🔧 Setting up LangSmith tracing with flag enabled...")
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        print("✅ LangSmith tracing configured")
    else:
        print("⚠️ LANGSMITH_TRACING not enabled")
    
    agent = Agent(
        name="Test Agent with Tracing Flag",
        instructions="You are a helpful assistant. Answer questions briefly and mention your name.",
        model="gpt-4o-mini"
    )
    
    print("\n🤖 Running agent test with tracing flag...")
    result = await Runner.run(
        starting_agent=agent,
        input="What is the capital of France? Please also tell me your name."
    )
    
    print(f"🎯 Result: {result.final_output}")
    print("✅ Test completed - check LangSmith dashboard for traces")
    print(f"🌐 Project: {os.getenv('LANGSMITH_PROJECT')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_with_tracing_flag())