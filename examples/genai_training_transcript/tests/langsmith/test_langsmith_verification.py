#!/usr/bin/env python3
"""
Test LangSmith tracing and verify traces appear
"""

import os
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

from agents import Agent, Runner, set_trace_processors
from langsmith.wrappers import OpenAIAgentsTracingProcessor
from langsmith import Client

async def test_and_verify_traces():
    """Test agent and verify traces appear in LangSmith"""
    
    print("🔧 Setting up test with trace verification...")
    
    # Set up tracing
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    
    # Create a unique test identifier
    test_id = f"test_{int(time.time())}"
    
    agent = Agent(
        name=f"Verification Agent {test_id}",
        instructions=f"You are a test agent with ID {test_id}. Always mention this ID in your response.",
        model="gpt-4o-mini"
    )
    
    print(f"🤖 Running agent test with ID: {test_id}")
    start_time = datetime.now()
    
    result = await Runner.run(
        starting_agent=agent,
        input=f"Please respond with a greeting and mention your test ID {test_id}"
    )
    
    end_time = datetime.now()
    print(f"🎯 Agent result: {result.final_output}")
    
    # Wait a moment for traces to propagate
    print("⏳ Waiting 3 seconds for traces to propagate...")
    await asyncio.sleep(3)
    
    # Check for traces
    print("🔍 Checking LangSmith for traces...")
    try:
        client = Client()
        
        # Look for recent runs in the last minute
        runs = list(client.list_runs(
            project_name=os.getenv('LANGSMITH_PROJECT', 'story-ops'),
            start_time=start_time,
            limit=10
        ))
        
        print(f"📊 Found {len(runs)} runs since test start")
        
        # Look for our specific test
        test_runs = [run for run in runs if test_id in str(run.name or '')]
        
        if test_runs:
            print(f"✅ Found {len(test_runs)} runs matching test ID {test_id}")
            for run in test_runs:
                print(f"  📝 Run: {run.name} (ID: {run.id})")
        else:
            print(f"⚠️ No runs found matching test ID {test_id}")
            print("Recent runs:")
            for run in runs[:3]:
                print(f"  📝 {run.name} - {run.run_type} - {run.start_time}")
        
    except Exception as e:
        print(f"❌ Error checking traces: {e}")
    
    print(f"🌐 Check LangSmith dashboard: project '{os.getenv('LANGSMITH_PROJECT')}'")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_and_verify_traces())