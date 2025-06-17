#!/usr/bin/env python3
"""
Knowledge Bridge MCP Interface Usage Example

Demonstrates how to use the Knowledge MCP Server for content lookup and retrieval.
This example shows the integration patterns that will be used by Research Team agents.

Author: Sprint 1 Development Team
Reference: US-001 Knowledge Database MCP Interface
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge_bridge.mcp_interface import create_knowledge_mcp_server


def demonstrate_knowledge_mcp():
    """Main demonstration of Knowledge MCP Server functionality"""
    
    print("🔍 Knowledge Bridge MCP Interface Demo")
    print("=" * 50)
    
    # Initialize MCP server with training manager output
    output_path = "output"  # Adjust path as needed
    mcp_server = create_knowledge_mcp_server(output_path)
    
    print(f"\n📊 Server initialized with output path: {output_path}")
    
    # 1. Health Check
    print("\n1️⃣ Health Check")
    print("-" * 20)
    health = mcp_server.health_check()
    print(f"Server Status: {health.get('server_status')}")
    if 'content_accessor' in health:
        accessor_health = health['content_accessor']
        print(f"Available Courses: {accessor_health.get('available_courses', 0)}")
        print(f"Total Modules: {accessor_health.get('total_modules', 0)}")
    
    # 2. List Available Operations
    print("\n2️⃣ Available MCP Operations")
    print("-" * 30)
    operations = mcp_server.list_operations()
    for op in operations:
        print(f"• {op['name']}: {op['description']}")
    
    # 3. Example Knowledge Lookup
    print("\n3️⃣ Knowledge Lookup Example")
    print("-" * 30)
    
    # Search for content related to machine learning
    search_keywords = ["machine learning", "algorithms", "AI"]
    learning_objectives = [
        "Learn basic machine learning concepts",
        "Understand supervised and unsupervised learning"
    ]
    
    print(f"Searching for: {search_keywords}")
    print(f"Learning objectives: {learning_objectives}")
    
    lookup_response = mcp_server.lookup_content(
        keywords=search_keywords,
        learning_objectives=learning_objectives,
        max_results=5
    )
    
    print(f"\nQuery ID: {lookup_response.get('query_id')}")
    print(f"Total Matches: {lookup_response.get('total_matches')}")
    
    # Display content matches
    content_matches = lookup_response.get('content_matches', [])
    for i, match in enumerate(content_matches, 1):
        print(f"\n  Match {i}:")
        print(f"    Content ID: {match.get('content_id')}")
        print(f"    Title: {match.get('title')}")
        print(f"    Relevance: {match.get('relevance_score', 0):.2f}")
        print(f"    Preview: {match.get('content_preview', '')[:100]}...")
        
        metadata = match.get('metadata', {})
        if metadata:
            print(f"    Source: {metadata.get('source')}")
            print(f"    Tags: {', '.join(metadata.get('tags', []))}")
    
    # 4. Content Retrieval Example
    print("\n4️⃣ Content Retrieval Example")
    print("-" * 30)
    
    if content_matches:
        # Get full content for the first match
        first_match_id = content_matches[0].get('content_id')
        print(f"Retrieving full content for: {first_match_id}")
        
        content_data = mcp_server.read_content(first_match_id)
        
        if content_data:
            print(f"\nContent ID: {content_data.get('content_id')}")
            
            metadata = content_data.get('metadata', {})
            print(f"Title: {metadata.get('title')}")
            print(f"Word Count: {metadata.get('word_count')}")
            print(f"Duration: {metadata.get('duration_minutes')} minutes")
            
            full_content = content_data.get('full_content', '')
            print(f"\nContent Preview (first 500 chars):")
            print("-" * 40)
            print(full_content[:500] + "..." if len(full_content) > 500 else full_content)
        else:
            print("❌ Content not found")
    else:
        print("ℹ️ No content matches found to retrieve")
    
    # 5. Integration Pattern Example
    print("\n5️⃣ Research Team Integration Pattern")
    print("-" * 40)
    
    def simulate_research_team_query(syllabus_section):
        """Simulate how Research Team would use MCP server"""
        print(f"📚 Researching: {syllabus_section['title']}")
        
        # Extract keywords from syllabus section
        keywords = syllabus_section.get('key_topics', [])
        learning_objectives = syllabus_section.get('learning_objectives', [])
        
        # Query knowledge base
        response = mcp_server.lookup_content(
            keywords=keywords,
            learning_objectives=learning_objectives,
            max_results=3
        )
        
        print(f"   Found {response.get('total_matches')} relevant sources")
        
        # Process results into research notes format
        research_references = []
        for match in response.get('content_matches', []):
            research_references.append({
                "content_id": match.get('content_id'),
                "relevance": match.get('relevance_score'),
                "title": match.get('title')
            })
        
        return research_references
    
    # Example syllabus section
    example_section = {
        "title": "Introduction to Machine Learning",
        "key_topics": ["supervised learning", "algorithms", "data science"],
        "learning_objectives": [
            "Understand basic ML concepts",
            "Learn about different types of algorithms"
        ]
    }
    
    research_refs = simulate_research_team_query(example_section)
    print(f"   Research references generated: {len(research_refs)}")
    for ref in research_refs:
        print(f"     - {ref['title']} (relevance: {ref['relevance']:.2f})")
    
    # 6. Schema Information
    print("\n6️⃣ MCP Schema Information")
    print("-" * 30)
    schemas = mcp_server.get_schemas()
    print(f"Available schemas: {', '.join(schemas.keys())}")
    
    print("\n✅ Knowledge Bridge MCP Demo Complete!")
    print("\nThis demonstrates the MCP interface that Research Team agents")
    print("will use to query the knowledge base for content synthesis.")


if __name__ == "__main__":
    try:
        demonstrate_knowledge_mcp()
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("\nNote: This demo requires training manager output data.")
        print("Run the training manager first to generate test data.")
        sys.exit(1)