#!/usr/bin/env python3
"""
Direct LangSmith client test to verify connectivity
"""

import os
import asyncio
from dotenv import load_dotenv, find_dotenv

# Load environment
load_dotenv(find_dotenv())

from langsmith import Client

def test_langsmith_client():
    """Test direct LangSmith client connectivity"""
    
    print("🔧 Testing direct LangSmith client...")
    
    api_key = os.getenv('LANGSMITH_API_KEY')
    project = os.getenv('LANGSMITH_PROJECT', 'story-ops')
    
    print(f"🌟 Project: {project}")
    print(f"🔑 API key: {'✅ Set' if api_key else '❌ Missing'}")
    
    if not api_key:
        print("❌ LANGSMITH_API_KEY not found")
        return False
    
    try:
        # Initialize client
        client = Client(api_key=api_key)
        
        # Test basic connectivity
        print("🔍 Testing LangSmith connectivity...")
        
        # Create a simple test run
        run = client.create_run(
            name="test_langsmith_connectivity",
            run_type="chain",
            inputs={"test": "connectivity check"},
            project_name=project
        )
        
        print(f"✅ Run created: {run.id}")
        
        # End the run
        client.update_run(
            run_id=run.id,
            outputs={"result": "LangSmith connectivity verified"},
            end_time=None
        )
        
        print(f"✅ LangSmith connectivity test successful!")
        print(f"🌐 Check your LangSmith dashboard for run: {run.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangSmith connectivity failed: {e}")
        return False

if __name__ == "__main__":
    test_langsmith_client()