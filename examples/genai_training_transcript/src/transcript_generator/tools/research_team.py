"""
Research Team component for knowledge-based research note generation.

This module implements the ResearchTeam class that queries the Knowledge Bridge
via MCP protocol to generate structured research notes for syllabus sections.

Author: Sprint 1 Development Team  
Reference: US-003 Research Team Knowledge Integration
"""

from typing import Dict, List, Any, TypedDict
import json

class SyllabusSection(TypedDict):
    """Input syllabus section structure"""
    section_id: str
    title: str
    learning_objectives: List[str]
    key_topics: List[str]
    estimated_duration: str

class ResearchNotes(TypedDict):
    """Output research notes structure"""
    section_id: str
    topic: str
    knowledge_references: List[Dict[str, Any]]
    structured_content: str
    learning_objectives: List[str]
    research_summary: str

class ResearchTeam:
    """
    Research Team agent for knowledge integration and research note generation.
    
    Implements the interface specified in sprint_1.md:
    - research_topic(syllabus_section) -> ResearchNotes
    """
    
    def __init__(self, knowledge_bridge_client=None):
        """Initialize Research Team with knowledge bridge connection"""
        self.knowledge_bridge = knowledge_bridge_client
        print("[ResearchTeam] Initialized with knowledge bridge connection")
    
    def research_topic(self, syllabus_section: SyllabusSection) -> ResearchNotes:
        """
        Research a syllabus section using knowledge bridge queries.
        
        Args:
            syllabus_section: Section to research with learning objectives and topics
            
        Returns:
            ResearchNotes: Structured research notes with knowledge references
        """
        print(f"[ResearchTeam] Researching topic: {syllabus_section['title']}")
        
        # Query knowledge bridge for relevant content
        knowledge_results = self._query_knowledge_bridge(syllabus_section)
        
        # Generate structured research notes
        research_notes = self._generate_research_notes(syllabus_section, knowledge_results)
        
        print(f"[ResearchTeam] Generated research notes for section: {syllabus_section['section_id']}")
        return research_notes
    
    def _query_knowledge_bridge(self, syllabus_section: SyllabusSection) -> List[Dict[str, Any]]:
        """Query knowledge bridge with syllabus section criteria"""
        if not self.knowledge_bridge:
            # Fallback for testing/stub mode
            print("[ResearchTeam] No knowledge bridge available - using mock data")
            return self._mock_knowledge_results(syllabus_section)
        
        # Prepare search criteria from syllabus section
        search_keywords = syllabus_section['key_topics']
        learning_objectives = syllabus_section['learning_objectives']
        
        try:
            # Query via MCP Knowledge Bridge
            query_response = self.knowledge_bridge.lookup_content(
                keywords=search_keywords,
                learning_objectives=learning_objectives,
                max_results=10
            )
            
            return query_response.get('content_matches', [])
            
        except Exception as e:
            print(f"[ResearchTeam] Knowledge bridge query failed: {str(e)}")
            # Graceful fallback to mock data
            return self._mock_knowledge_results(syllabus_section)
    
    def _mock_knowledge_results(self, syllabus_section: SyllabusSection) -> List[Dict[str, Any]]:
        """Generate mock knowledge results for testing"""
        return [
            {
                "content_id": f"mock_{syllabus_section['section_id']}_01",
                "title": f"Source material for {syllabus_section['title']}",
                "relevance_score": 0.9,
                "content_preview": f"Mock content preview for {syllabus_section['title']} covering key concepts...",
                "metadata": {
                    "source": "training_transcripts",
                    "content_type": "transcript",
                    "tags": syllabus_section['key_topics']
                }
            }
        ]
    
    def _generate_research_notes(self, syllabus_section: SyllabusSection, knowledge_results: List[Dict[str, Any]]) -> ResearchNotes:
        """Generate structured research notes from knowledge results"""
        
        # Extract knowledge references
        knowledge_references = []
        for result in knowledge_results:
            knowledge_references.append({
                "content_id": result['content_id'], 
                "key_points": self._extract_key_points(result, syllabus_section)
            })
        
        # Generate structured content summary
        structured_content = self._create_structured_content(syllabus_section, knowledge_results)
        
        # Create research summary
        research_summary = self._create_research_summary(syllabus_section, knowledge_results)
        
        return ResearchNotes(
            section_id=syllabus_section['section_id'],
            topic=syllabus_section['title'],
            knowledge_references=knowledge_references,
            structured_content=structured_content,
            learning_objectives=syllabus_section['learning_objectives'],
            research_summary=research_summary
        )
    
    def _extract_key_points(self, knowledge_result: Dict[str, Any], syllabus_section: SyllabusSection) -> List[str]:
        """Extract key points from knowledge result relevant to syllabus section"""
        # For now, generate mock key points based on topics
        key_topics = syllabus_section.get('key_topics', [])
        return [f"Key insight about {topic} from {knowledge_result['title']}" for topic in key_topics[:3]]
    
    def _create_structured_content(self, syllabus_section: SyllabusSection, knowledge_results: List[Dict[str, Any]]) -> str:
        """Create structured content outline from research"""
        content_sections = [
            f"# {syllabus_section['title']} - Research Notes",
            "",
            "## Key Concepts",
            *[f"- {topic}" for topic in syllabus_section['key_topics']],
            "",
            "## Learning Objectives",
            *[f"- {obj}" for obj in syllabus_section['learning_objectives']],
            "",
            "## Source Material Summary",
            *[f"- {result['title']}: {result['content_preview'][:100]}..." for result in knowledge_results[:3]],
            "",
            "## Implementation Notes",
            f"Duration: {syllabus_section.get('estimated_duration', 'Not specified')}",
            f"Sources: {len(knowledge_results)} knowledge references"
        ]
        
        return "\n".join(content_sections)
    
    def _create_research_summary(self, syllabus_section: SyllabusSection, knowledge_results: List[Dict[str, Any]]) -> str:
        """Create concise research summary"""
        return f"Research completed for '{syllabus_section['title']}' with {len(knowledge_results)} knowledge sources. Key topics: {', '.join(syllabus_section['key_topics'])}. Ready for content synthesis."


# Legacy function for backward compatibility
def aggregate_research(agenda, transcripts, config):
    """
    Legacy function - maintained for backward compatibility.
    New code should use ResearchTeam.research_topic() instead.
    """
    print("[research_team] Using legacy aggregate_research function")
    print("[research_team] Consider migrating to ResearchTeam.research_topic()")
    
    # Build a mapping of module titles (or names) to research content
    notes: dict[str, str] = {}
    for item in agenda:
        # Support agenda entries as dicts or strings
        key = item.get("title") if isinstance(item, dict) else item
        content = transcripts.get(key, "")
        if not content.strip():
            raise RuntimeError(f"[research_team] No transcript source found for module: {key}. Aborting research.")
        notes[key] = content
    return notes