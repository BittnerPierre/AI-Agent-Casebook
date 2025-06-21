#!/usr/bin/env python3
"""
End-to-End CLI Integration Test

Tests the complete user experience via the CLI interface.
This is the ultimate integration test that validates the entire system
from CLI input to final output generation.
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from test_utils import evaluate_critical_test_success

def run_cli_end_to_end_test():
    """Run complete end-to-end test via CLI"""
    print("🚀 Starting End-to-End CLI Integration Test")
    print("=" * 60)
    
    # Use generated_content directory for transcript generator outputs
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "generated_content"
    
    print(f"📁 Using output directory: {output_dir}")
    
    # Test configuration
    syllabus_path = base_dir / "syllabus.md"
    cli_script = base_dir / "cli" / "transcript_generator_cli.py"
    
    if not syllabus_path.exists():
        print(f"❌ Syllabus not found at {syllabus_path}")
        return False
        
    if not cli_script.exists():
        print(f"❌ CLI script not found at {cli_script}")
        return False
        
    print(f"✅ Found syllabus: {syllabus_path}")
    print(f"✅ Found CLI script: {cli_script}")
    
    # Build CLI command
    cmd = [
        "poetry", "run", "python", str(cli_script),
        "--syllabus", str(syllabus_path),
        "--output-dir", str(output_dir),
        "--overwrite",
        "--timeout", "120",  # 2 minutes per phase
        "--continue-on-errors",
        "--verbose"
    ]
    
    print(f"\n🔧 CLI Command:")
    print(f"   {' '.join(cmd)}")
    
    # Set up environment
    env = os.environ.copy()
    
    # Check for .env file
    env_file = base_dir / ".env"
    if env_file.exists():
        print(f"✅ Using local .env file: {env_file}")
        # Load .env manually since subprocess doesn't auto-load it
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env[key] = value
    else:
        print("⚠️  No local .env file found")
        
    # Check if API key is available
    if 'OPENAI_API_KEY' in env:
        print("✅ OPENAI_API_KEY available for real API testing")
    else:
        print("⚠️  OPENAI_API_KEY not available - may run in simulation mode")
        
    try:
        print(f"\n⚡ Executing CLI workflow...")
        print(f"⏱️  Timeout: 10 minutes total")
        
        start_time = time.time()
        
        # Run the CLI command
        result = subprocess.run(
            cmd,
            cwd=str(base_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes total timeout
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
            
        print(f"\n📊 CLI Execution Results:")
        print("=" * 40)
        print(f"Return Code: {result.returncode}")
        print(f"Execution Time: {execution_time:.2f} seconds")
        
        # Show stdout
        if result.stdout:
            print(f"\n📄 CLI Output:")
            print("-" * 30)
            print(result.stdout[-2000:])  # Last 2000 chars to avoid overflow
            
        # Show stderr if there are errors
        if result.stderr:
            print(f"\n🚨 CLI Errors/Warnings:")
            print("-" * 30) 
            print(result.stderr[-1000:])  # Last 1000 chars
            
        # Validate outputs
        print(f"\n🔍 Validating Outputs...")
        print("-" * 30)
        
        success_criteria = {
            "cli_exit_success": result.returncode == 0,
            "core_functionality": result.returncode == 0,  # Critical: CLI must work
            "output_dir_created": output_dir.exists(),
            "execution_time_reasonable": execution_time < 600,  # 10 minutes max
        }
        
        # Check for expected output files
        if output_dir.exists():
            output_files = list(output_dir.rglob("*"))
            success_criteria["output_files_created"] = len(output_files) > 0
            print(f"   📁 Output files created: {len(output_files)}")
            
            # Look for specific expected outputs
            expected_outputs = [
                "*.md",      # Final transcripts
                "*.json",    # Metadata and quality reports
                "research_notes",  # Research phase outputs
                "quality_issues"   # Quality assessment outputs
            ]
            
            for pattern in expected_outputs:
                matches = list(output_dir.rglob(pattern))
                if matches:
                    print(f"   ✅ Found {pattern}: {len(matches)} files")
                else:
                    print(f"   ⚠️  Missing {pattern}")
                    
        else:
            success_criteria["output_files_created"] = False
            print(f"   ❌ Output directory not created")
            
        # Check for LangSmith integration evidence
        langsmith_evidence = False
        if result.stdout and ("langsmith" in result.stdout.lower() or "evaluation" in result.stdout.lower()):
            langsmith_evidence = True
            print(f"   ✅ LangSmith integration evidence found in output")
        else:
            print(f"   ⚠️  No LangSmith integration evidence in output")
            
        success_criteria["langsmith_integration"] = langsmith_evidence
        
        # Use strict evaluation criteria from test_utils
        is_success, message = evaluate_critical_test_success(
            result, 
            success_criteria, 
            critical_keys=["cli_exit_success", "core_functionality"]
        )
        
        print(f"\n📈 Evaluation Result: {message}")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion.replace('_', ' ').title()}")
            
        # Overall result
        print(f"\n" + "=" * 60)
        if is_success:
            print(f"🎉 END-TO-END CLI TEST PASSED")
            print(f"✅ System ready for production use")
            return True
        else:
            print(f"❌ END-TO-END CLI TEST FAILED")
            print(f"🚨 Critical issues detected - requires fixes")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏰ CLI test timed out after 10 minutes")
        print(f"❌ This may indicate performance issues or hanging processes")
        return False
        
    except Exception as e:
        print(f"\n💥 CLI test crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 End-to-End CLI Integration Test")
    print("Testing complete user workflow via CLI interface")
    print()
    
    success = run_cli_end_to_end_test()
    
    if success:
        print(f"\n🎯 CLI integration test completed successfully!")
        print(f"🚀 System is ready for UAT")
        exit(0)
    else:
        print(f"\n💀 CLI integration test failed!")
        print(f"🔧 Review issues before proceeding to UAT")
        exit(1)