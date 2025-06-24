"""
Test Agent SDK availability and basic imports
"""

import sys
import inspect

def test_agent_sdk_imports():
    """Test if Agent SDK can be imported and basic functionality works"""
    
    print("🧪 Testing Agent SDK Availability")
    print("=" * 50)
    
    # Test 1: Basic imports
    try:
        from agents import Agent, Runner, function_tool
        print("✅ Agent SDK imports successful")
        print(f"   - Agent: {Agent}")
        print(f"   - Runner: {Runner}")  
        print(f"   - function_tool: {function_tool}")
    except ImportError as e:
        print(f"❌ Agent SDK import failed: {e}")
        return False
    
    # Test 2: Check Runner.run is async
    try:
        is_async = inspect.iscoroutinefunction(getattr(Runner, "run", None))
        print(f"✅ Runner.run is async: {is_async}")
    except Exception as e:
        print(f"❌ Runner.run check failed: {e}")
        return False
    
    # Test 3: Check advanced imports
    try:
        from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
        print("✅ Advanced imports (handoff_prompt) successful")
    except ImportError as e:
        print(f"⚠️  Advanced imports failed (optional): {e}")
    
    # Test 4: Check Pydantic integration
    try:
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            test_field: str = Field(description="Test field")
        
        print("✅ Pydantic integration available")
    except Exception as e:
        print(f"❌ Pydantic integration failed: {e}")
        return False
    
    # Test 5: Check function_tool decorator
    try:
        @function_tool
        def test_function_tool(test_param: str) -> str:
            """Test function tool"""
            return f"Test result: {test_param}"
        
        print("✅ Function tool decorator works")
        print(f"   - Decorated function: {test_function_tool}")
    except Exception as e:
        print(f"❌ Function tool decorator failed: {e}")
        return False
    
    # Test 6: Agent creation (without API key)
    try:
        from pydantic import BaseModel
        
        class TestOutput(BaseModel):
            result: str
        
        test_agent = Agent(
            name="TestAgent",
            instructions="Test agent for validation",
            model="gpt-4o-mini",
            output_type=TestOutput
        )
        print("✅ Agent creation successful (without API key)")
        print(f"   - Agent name: {test_agent.name}")
        print(f"   - Agent model: {test_agent.model}")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False
    
    print("\n🎉 All Agent SDK tests passed!")
    print("📝 Next steps:")
    print("   1. Set OPENAI_API_KEY environment variable")
    print("   2. Run minimal_research_workflow.py")
    print("   3. Verify multi-agent workflow execution")
    
    return True

def show_environment_info():
    """Show Python environment information"""
    print("\n📊 Environment Information")
    print("=" * 30)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    try:
        import openai
        print(f"OpenAI library version: {openai.__version__}")
    except:
        print("OpenAI library: Not available")
    
    try:
        import agents
        print(f"Agents SDK available: Yes")
        # Try to get version if available
        if hasattr(agents, '__version__'):
            print(f"Agents SDK version: {agents.__version__}")
    except:
        print("Agents SDK: Not available")

if __name__ == "__main__":
    success = test_agent_sdk_imports()
    show_environment_info()
    
    if success:
        print("\n✅ Agent SDK environment is ready!")
        print("🔑 Set OPENAI_API_KEY to run full workflow tests")
    else:
        print("\n❌ Agent SDK environment has issues")
        print("🔧 Please check Agent SDK installation")