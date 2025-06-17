#!/usr/bin/env python3
"""
Response API File_Search Integration Example

This example demonstrates how to use OpenAI's Response API with file_search
capabilities for content synthesis, specifically showing the pattern that
will be used in US-004 for research note synthesis.

Configuration:
- Project ID: proj_UWuOPp9MOKrOCtZABSCTY4Um
- Environment: OPENAI_API_KEY must be set
- Usage: Research notes → Chapter synthesis pattern

Author: Sprint 1 Development Team
Reference: US-011 Response API File_Search Integration Pattern
"""

import os
import json
from typing import Dict, List, Any
from openai import OpenAI

def create_sample_research_notes() -> Dict[str, Any]:
    """Create sample research notes for demonstration"""
    return {
        "topic": "Prompt Engineering for Developers",
        "knowledge_references": [
            "system_vs_user_prompts.md",
            "few_shot_techniques.md", 
            "chain_of_thought_prompting.md"
        ],
        "structured_content": """
# Prompt Engineering for Developers - Research Notes

## Key Concepts
- System prompts: Define role and context for AI assistant
- User prompts: Specific instructions or questions from end user
- Zero-shot: No examples provided, direct instruction
- Few-shot: Include 1-3 examples to guide response format
- Chain-of-Thought: Step-by-step reasoning process

## Practical Techniques
1. **Template Structure**: Use consistent format for system prompts
2. **Context Setting**: Provide relevant background information
3. **Output Formatting**: Specify desired response structure
4. **Error Handling**: Include fallback instructions

## Developer Applications
- API integration patterns
- Prompt template libraries
- Response validation techniques
- Iterative prompt refinement
        """,
        "learning_objectives": [
            "Understand difference between system and user prompts",
            "Apply few-shot prompting techniques",
            "Implement Chain-of-Thought reasoning patterns",
            "Practice iterative prompt optimization"
        ]
    }

def setup_file_search_assistant(client: OpenAI) -> str:
    """Create an assistant with file_search capability"""
    
    # Create sample research notes file for upload
    sample_notes = create_sample_research_notes()
    
    # Save to temporary file for upload
    temp_file_path = "/tmp/sample_research_notes.json"
    with open(temp_file_path, 'w') as f:
        json.dump(sample_notes, f, indent=2)
    
    try:
        # Upload the file
        with open(temp_file_path, 'rb') as f:
            file_obj = client.files.create(
                file=f,
                purpose='assistants'
            )
        
        # Create assistant with file_search tool
        assistant = client.beta.assistants.create(
            name="Research Notes Synthesizer",
            instructions="""You are an expert content creator specializing in educational training materials. 
            Your role is to synthesize research notes into engaging, well-structured chapter content 
            following training course narrative principles.
            
            When provided with research notes, create educational content that:
            1. Follows learning progression from basic to advanced concepts
            2. Includes practical hands-on examples
            3. Maintains engagement through varied content formats
            4. Aligns with specified learning objectives
            
            Use the uploaded research notes to inform your content synthesis.""",
            model="gpt-4-turbo-preview",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": []
                }
            }
        )
        
        # Create vector store and add file
        vector_store = client.beta.vector_stores.create(
            name="Research Notes Store"
        )
        
        # Add file to vector store
        client.beta.vector_stores.files.create(
            vector_store_id=vector_store.id,
            file_id=file_obj.id
        )
        
        # Update assistant with vector store
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store.id]
                }
            }
        )
        
        print(f"✅ Assistant created with ID: {assistant.id}")
        print(f"✅ Vector store created with ID: {vector_store.id}")
        print(f"✅ File uploaded with ID: {file_obj.id}")
        
        return assistant.id
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def synthesize_chapter_content(client: OpenAI, assistant_id: str, syllabus_section: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize chapter content using file_search on research notes"""
    
    # Create thread for conversation
    thread = client.beta.threads.create()
    
    # Create synthesis prompt based on syllabus section
    synthesis_prompt = f"""
Based on the research notes available, create a comprehensive training chapter for:

**Module:** {syllabus_section.get('title', 'Unknown Module')}
**Duration:** {syllabus_section.get('duration', 'Not specified')}
**Objectives:** {', '.join(syllabus_section.get('objectives', []))}

Please synthesize the research notes into a well-structured training chapter that includes:

1. **Introduction** - Context and relevance
2. **Core Concepts** - Key learning points with clear explanations  
3. **Practical Examples** - Hands-on demonstrations
4. **Exercises** - Interactive learning activities
5. **Summary** - Key takeaways and next steps

Ensure the content:
- Aligns with the specified learning objectives
- Maintains appropriate depth for the target duration
- Follows educational best practices for engagement
- References the research notes appropriately

Format the response as a structured training chapter ready for delivery.
"""
    
    # Send message to assistant
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=synthesis_prompt
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion
    import time
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    
    if run.status == 'completed':
        # Get messages
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Extract assistant response
        assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']
        if assistant_messages:
            content = assistant_messages[0].content[0].text.value
            
            # Structure the response
            chapter_draft = {
                "chapter_title": syllabus_section.get('title', 'Generated Chapter'),
                "content": content,
                "duration_estimate": syllabus_section.get('duration', 60),  # minutes
                "source_references": ["research_notes.json"],
                "synthesis_metadata": {
                    "thread_id": thread.id,
                    "run_id": run.id,
                    "model_used": "gpt-4-turbo-preview",
                    "file_search_used": True
                }
            }
            
            return chapter_draft
    
    else:
        raise Exception(f"Run failed with status: {run.status}")

def demonstrate_file_search_pattern():
    """Main demonstration of the file_search pattern"""
    
    # Verify environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize client with project ID
    client = OpenAI(
        api_key=api_key,
        default_headers={
            "OpenAI-Project": "proj_UWuOPp9MOKrOCtZABSCTY4Um"
        }
    )
    
    print("🚀 Starting Response API File_Search Demonstration")
    print("=" * 60)
    
    try:
        # Step 1: Setup assistant with file_search
        print("\n📁 Setting up assistant with file_search capability...")
        assistant_id = setup_file_search_assistant(client)
        
        # Step 2: Create sample syllabus section
        syllabus_section = {
            "title": "Prompt Engineering for Developers", 
            "duration": 120,  # 2 hours
            "objectives": [
                "Learn system vs. user prompts, zero-shot & few-shot techniques",
                "Practice Chain-of-Thought and ReAct prompting", 
                "Hands-on: iterate prompts to optimize responses"
            ]
        }
        
        # Step 3: Synthesize content
        print(f"\n⚙️  Synthesizing chapter content for: {syllabus_section['title']}")
        chapter_draft = synthesize_chapter_content(client, assistant_id, syllabus_section)
        
        # Step 4: Display results
        print("\n✅ Chapter synthesis completed!")
        print("=" * 60)
        print(f"Title: {chapter_draft['chapter_title']}")
        print(f"Duration: {chapter_draft['duration_estimate']} minutes")
        print(f"Sources: {', '.join(chapter_draft['source_references'])}")
        print("\nGenerated Content Preview:")
        print("-" * 40)
        print(chapter_draft['content'][:500] + "..." if len(chapter_draft['content']) > 500 else chapter_draft['content'])
        
        # Step 5: Save result for inspection
        output_file = "/tmp/synthesized_chapter.json"
        with open(output_file, 'w') as f:
            json.dump(chapter_draft, f, indent=2)
        
        print(f"\n💾 Full chapter saved to: {output_file}")
        print("\n🎯 Pattern demonstration complete!")
        print("This example shows the file_search integration pattern for US-004")
        
        return chapter_draft
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        result = demonstrate_file_search_pattern()
        print("\n✅ Response API File_Search example completed successfully")
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        exit(1)