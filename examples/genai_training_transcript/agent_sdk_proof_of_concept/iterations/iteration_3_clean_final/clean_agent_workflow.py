"""
Clean Agent SDK Proof-of-Concept for ResearchTeam Migration

Demonstrates proper agentic workflow with supervisor pattern using only KnowledgeRetriever.
Focus: Migration stub for existing code patterns, not over-engineering.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Agent SDK imports
try:
    from agents import Agent, Runner, function_tool
    from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
    AGENT_SDK_AVAILABLE = bool(os.environ.get("OPENAI_API_KEY"))
except ImportError:
    AGENT_SDK_AVAILABLE = False
    # Mock function_tool for fallback
    def function_tool(func):
        return func

# Use KnowledgeRetriever and MCP filesystem
from transcript_generator.tools.knowledge_retriever import KnowledgeRetriever
try:
    from agents.mcp import MCPServerStdio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Global knowledge retriever instance for function tools
_knowledge_retriever = KnowledgeRetriever("knowledge_db")

@function_tool
async def search_knowledge(keywords: List[str], limit: int = 5) -> str:
    """Search knowledge base for relevant content (Agent SDK function tool)"""
    try:
        content_sources = await _knowledge_retriever.get_related_content(keywords, limit)
        
        results = []
        for source in content_sources:
            results.append({
                "module_id": source.get("module_id"),
                "title": source.get("title"),
                "summary": source.get("summary"),
                "content_preview": source.get("content_preview", "")[:300],
                "keywords": source.get("keywords", [])
            })
        
        return json.dumps({
            "found_content": len(results),
            "sources": results
        }, indent=2)
    except Exception as e:
        return f"Error searching knowledge: {e}"

# Remove the function tool wrapper - MCP filesystem will be passed directly to agent


class AgentResearchWorkflow:
    """Clean Agent SDK workflow using function tools for knowledge access"""
    
    def __init__(self, knowledge_db_path: str = "knowledge_db"):
        # Create MCP filesystem server for research output
        self.output_dir = Path("agent_sdk_proof_of_concept/research_output")
        self.output_dir.mkdir(exist_ok=True)
        
        if AGENT_SDK_AVAILABLE and MCP_AVAILABLE:
            # Create MCP filesystem server
            self.mcp_filesystem_server = MCPServerStdio(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", str(self.output_dir)]
            )
            self._setup_agents()
        elif AGENT_SDK_AVAILABLE:
            self.mcp_filesystem_server = None
            self._setup_agents()
        else:
            self.mcp_filesystem_server = None
    
    def _setup_agents(self):
        """Setup agents with proper supervisor pattern"""
        
        # Supervisor Agent - coordinates research workflow
        self.supervisor = Agent(
            name="ResearchSupervisor",
            instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
            You are a Research Supervisor coordinating a multi-agent research workflow.
            
            Your responsibilities:
            1. Plan research strategy based on section topics
            2. Coordinate handoffs between specialist agents
            3. Ensure comprehensive coverage of learning objectives
            4. Make final decisions on research quality
            
            You work with specialized agents: Researcher, Analyst, Synthesizer.
            Always maintain research quality and educational value focus.""",
            model="gpt-4o-mini"
        )
        
        # Researcher Agent - content discovery via function tools
        self.researcher = Agent(
            name="ContentResearcher", 
            instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
            You are a Content Researcher specializing in educational material discovery.
            
            Your role:
            1. Use search_knowledge function tool to find relevant content
            2. Analyze learning topics and identify key concepts
            3. Assess content relevance to learning objectives
            4. Provide structured findings for analysis
            
            Always use the search_knowledge tool to find training content.
            Focus on educational value and learning objective alignment.""",
            model="gpt-4o-mini",
            tools=[search_knowledge]
        )
        
        # Analyst Agent - content analysis
        self.analyst = Agent(
            name="ContentAnalyst",
            instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
            You are a Content Analyst extracting learning insights from training materials.
            
            Your expertise:
            1. Analyze educational content for key learning points
            2. Extract pedagogical patterns and teaching methods
            3. Identify knowledge gaps and learning opportunities
            4. Structure findings for synthesis
            
            Extract insights valuable for training content creation.""",
            model="gpt-4o-mini"
        )
        
        # Synthesizer Agent - knowledge integration with MCP filesystem
        mcp_servers = [self.mcp_filesystem_server] if self.mcp_filesystem_server else []
        
        self.synthesizer = Agent(
            name="KnowledgeSynthesizer",
            instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
            You are a Knowledge Synthesizer creating coherent research summaries.
            
            Your approach:
            1. Integrate research findings into unified summaries
            2. Create actionable recommendations for content creators
            3. Maintain educational focus and learning objectives
            4. Use MCP filesystem to save research results as JSON files
            
            REQUIRED JSON SCHEMA for research notes (per specifications):
            {{
              "section_id": "string",
              "knowledge_references": [
                {{
                  "content_id": "string",
                  "key_points": ["string", "string", ...]
                }}
              ],
              "research_summary": "string"
            }}
            
            This EXACT schema is defined in Inter_Module_Architecture.md and MUST be followed.
            Do NOT add extra fields like "key_insights", "generated_by", etc.
            
            You MUST save the research notes using MCP filesystem tools in this exact JSON format.
            File name should be: {{section_id}}_research_notes.json""",
            model="gpt-4o-mini",
            mcp_servers=mcp_servers
        )
    
    async def research_topic(self, syllabus_section: Dict[str, Any]) -> Dict[str, Any]:
        """Execute supervised multi-agent research workflow"""
        
        if not AGENT_SDK_AVAILABLE:
            return self._fallback_research(syllabus_section)
        
        section_id = syllabus_section.get("section_id")
        key_topics = syllabus_section.get("key_topics", [])
        
        print(f"\n🎯 Starting Supervised Agent Research Workflow")
        print(f"📖 Section: {section_id}")
        print(f"🎯 Topics: {', '.join(key_topics)}")
        print("=" * 60)
        
        # Phase 1: Supervisor plans research strategy
        print("\n👑 Phase 1: Supervisor Planning")
        
        planning_context = f"""
        RESEARCH PLANNING REQUEST
        
        Section: {section_id}
        Key Topics: {key_topics}
        
        Task: Plan research strategy for this section. Consider:
        1. What specific aspects of these topics need investigation?
        2. How should the research be structured for educational value?
        3. What handoff sequence will ensure comprehensive coverage?
        
        Provide research plan and handoff strategy.
        """
        
        planning_result = await Runner.run(
            starting_agent=self.supervisor,
            input=planning_context
        )
        
        research_plan = planning_result.final_output
        print(f"✅ Research plan created")
        
        # Phase 2: Knowledge Discovery (Researcher uses function tools)
        print("\n🔍 Phase 2: Content Discovery")
        
        research_context = f"""
        CONTENT RESEARCH REQUEST
        
        Research Plan: {research_plan}
        Target Topics: {key_topics}
        
        Task: Use the search_knowledge function tool to find relevant training content.
        Search for content related to: {', '.join(key_topics)}
        
        Then analyze the found content and assess relevance for learning objectives.
        Focus on educational value and topic coverage.
        
        HANDOFF TO: ContentAnalyst for detailed content analysis.
        """
        
        research_result = await Runner.run(
            starting_agent=self.researcher,
            input=research_context
        )
        
        research_findings = research_result.final_output
        print(f"✅ Content research completed")
        
        # Phase 3: Content Analysis (Analyst)
        print("\n🧠 Phase 3: Content Analysis")
        
        analysis_context = f"""
        CONTENT ANALYSIS REQUEST
        
        Research Findings: {research_findings}
        
        Task: Extract key learning insights and educational patterns from the research findings.
        The researcher has already used function tools to find relevant content.
        Analyze their findings to identify the most valuable content for training development.
        
        HANDOFF TO: KnowledgeSynthesizer for final integration.
        """
        
        analysis_result = await Runner.run(
            starting_agent=self.analyst,
            input=analysis_context
        )
        
        analysis_findings = analysis_result.final_output
        print(f"✅ Content analysis completed")
        
        # Phase 4: Knowledge Synthesis (Synthesizer with tools)
        print("\n🎨 Phase 4: Knowledge Synthesis")
        
        synthesis_context = f"""
        KNOWLEDGE SYNTHESIS REQUEST
        
        Section: {section_id}
        Research Plan: {research_plan}
        Research Findings: {research_findings}
        Analysis Results: {analysis_findings}
        
        Task: Create coherent research summary integrating all findings.
        Use MCP filesystem to save the results as a JSON file.
        
        Required actions:
        1. Synthesize all research and analysis into unified summary
        2. Create actionable insights for content creators
        3. Save results using MCP filesystem tools (write file: {section_id}_research_notes.json)
        4. Confirm completion to supervisor
        """
        
        synthesis_result = await Runner.run(
            starting_agent=self.synthesizer,
            input=synthesis_context
        )
        
        synthesis_output = synthesis_result.final_output
        print(f"✅ Knowledge synthesis completed")
        
        # Phase 5: Supervisor Review
        print("\n👑 Phase 5: Supervisor Review")
        
        review_context = f"""
        RESEARCH REVIEW REQUEST
        
        Original Plan: {research_plan}
        Research Findings: {research_findings}
        Analysis Results: {analysis_findings}
        Synthesis Output: {synthesis_output}
        
        Task: Review completed research workflow and provide final assessment.
        Ensure all learning objectives were addressed and quality standards met.
        """
        
        review_result = await Runner.run(
            starting_agent=self.supervisor,
            input=review_context
        )
        
        final_assessment = review_result.final_output
        print(f"✅ Supervisor review completed")
        
        # Return structured results (matching existing ResearchTeam format)
        return {
            "section_id": section_id,
            "research_summary": synthesis_output,
            "knowledge_references": [
                {
                    "content_id": "agent_discovered_content",
                    "title": "Content discovered via function tools",
                    "summary": "Content found using search_knowledge function tool"
                }
            ],
            "supervisor_assessment": final_assessment,
            "workflow_type": "Supervised Multi-Agent Research with Function Tools",
            "agents_used": ["ResearchSupervisor", "ContentResearcher", "ContentAnalyst", "KnowledgeSynthesizer"],
            "function_tools_used": ["search_knowledge"],
            "mcp_servers_used": ["filesystem"] if self.mcp_filesystem_server else []
        }
    
    def _format_content_sources(self, content_sources: List[Dict[str, Any]]) -> str:
        """Format content sources for agent context"""
        if not content_sources:
            return "No relevant content sources found."
        
        formatted = []
        for source in content_sources[:3]:  # Limit for context
            title = source.get("title", "Unknown")
            module_id = source.get("module_id", "unknown")
            summary = source.get("summary", "")[:100]
            formatted.append(f"- {title} (ID: {module_id})\n  Summary: {summary}...")
        
        return "\n".join(formatted)
    
    def _format_detailed_content(self, content_sources: List[Dict[str, Any]]) -> str:
        """Format detailed content for analysis"""
        if not content_sources:
            return "No content available for analysis."
        
        formatted = []
        for source in content_sources[:2]:  # Limit for context size
            title = source.get("title", "Unknown")
            preview = source.get("content_preview", "")
            keywords = ", ".join(source.get("keywords", [])[:5])
            formatted.append(f"Content: {title}\nKeywords: {keywords}\nPreview: {preview[:300]}...")
        
        return "\n\n".join(formatted)
    
    def _fallback_research(self, syllabus_section: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback when Agent SDK not available"""
        section_id = syllabus_section.get("section_id")
        key_topics = syllabus_section.get("key_topics", [])
        
        return {
            "section_id": section_id,
            "research_summary": f"[FALLBACK] Basic research for {section_id} covering {', '.join(key_topics)}",
            "knowledge_references": [],
            "workflow_type": "Fallback (No Agent SDK)",
            "agents_used": []
        }


async def main():
    """Test the clean Agent SDK research workflow"""
    
    print("🚀 Testing Clean Agent SDK Research Workflow")
    print("=" * 60)
    
    if not AGENT_SDK_AVAILABLE:
        print("⚠️  Agent SDK not available - will run fallback")
    else:
        print("✅ Agent SDK available")
    
    # Initialize workflow with KnowledgeRetriever
    workflow = AgentResearchWorkflow()
    
    # Test research workflow
    test_section = {
        "section_id": "multi_agent_coordination", 
        "key_topics": ["multi agent", "agent coordination", "handoffs"]
    }
    
    try:
        results = await workflow.research_topic(test_section)
        
        print("\n📊 WORKFLOW RESULTS:")
        print("=" * 40)
        print(f"Section: {results['section_id']}")
        print(f"Workflow Type: {results['workflow_type']}")
        print(f"Agents Used: {', '.join(results['agents_used'])}")
        print(f"Knowledge References: {len(results['knowledge_references'])}")
        print(f"Summary Length: {len(results['research_summary'])} characters")
        
        if results.get('supervisor_assessment'):
            print(f"Supervisor Quality Check: ✅ Completed")
        
        print("\n✅ SUCCESS: Clean Agent SDK workflow completed!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())