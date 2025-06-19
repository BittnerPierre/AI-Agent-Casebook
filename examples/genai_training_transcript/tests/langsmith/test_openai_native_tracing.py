#!/usr/bin/env python3
"""
Test OpenAI Agents SDK native tracing to LangSmith
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

# Try using the built-in tracing from OpenAI Agents SDK
from agents import Agent, Runner, trace, gen_trace_id

async def test_native_tracing():
    """Test OpenAI Agents native tracing"""
    
    print("🔧 Testing OpenAI Agents SDK native tracing...")
    print(f"📊 Project: {os.getenv('LANGSMITH_PROJECT')}")
    
    # Generate trace ID
    trace_id = gen_trace_id()
    print(f"🆔 Generated trace ID: {trace_id}")
    
    agent = Agent(
        name="Native Trace Test Agent",
        instructions="You are a test agent for native tracing. Always mention tracing in your response.",
        model="gpt-4o-mini"
    )
    
    # Use the trace context manager
    with trace("test_native_langsmith_tracing", trace_id=trace_id):
        print("🎯 Running agent with native tracing context...")
        
        result = await Runner.run(
            starting_agent=agent,
            input="Hello! Please confirm you are part of a traced execution."
        )
        
        print(f"📝 Agent response: {result.final_output}")
        print(f"🔗 Trace ID: {trace_id}")
    
    return result, trace_id

if __name__ == "__main__":
    asyncio.run(test_native_tracing())