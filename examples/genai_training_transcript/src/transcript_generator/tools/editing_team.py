"""
Editing Team Implementation (US-004)

Multi-agent editing team using Response API file_search for content synthesis.
This class coordinates Documentalist, Writer, and Reviewer agents to process chapters.
"""

import logging
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI library not installed. Install with: pip install openai")

# Setup structured logging according to professional standards
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class ChapterDraft:
    """Chapter draft data structure according to schema specifications"""
    section_id: str
    content: str
    
    def to_dict(self) -> dict[str, str]:
        """Convert to dict for JSON serialization"""
        return {
            "section_id": self.section_id,
            "content": self.content
        }


@dataclass
class SynthesisRequest:
    """Request structure for content synthesis"""
    query: str
    type: str
    target_module: str
    
    def to_dict(self) -> dict[str, str]:
        """Convert to dict for processing"""
        return {
            "query": self.query,
            "type": self.type,
            "target_module": self.target_module
        }


class EditingTeam:
    """
    EditingTeam class implementing US-004 Response API Content Synthesis.
    
    Uses OpenAI Response API file_search on research notes for multi-step content generation.
    Coordinates Writer, Reviewer, and Script Strategist agents with agent-to-agent feedback loops.
    """
    
    def __init__(self, 
                 api_key: str | None = None,
                 project_id: str | None = None,
                 model: str = "gpt-4o-mini",
                 max_revisions: int = 2,
                 poll_interval_secs: float = 1.0,
                 expires_after_days: int = 1):
        """
        Initialize EditingTeam with Response API configuration.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            project_id: OpenAI project ID for Response API
            model: OpenAI model for synthesis (default: gpt-4o-mini)
            max_revisions: Maximum revision iterations per chapter
            poll_interval_secs: Polling interval for file batch processing
            expires_after_days: Vector store expiration in days
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.project_id = project_id or "proj_UWuOPp9MOKrOCtZABSCTY4Um"
        self.model = model
        self.max_revisions = max_revisions
        self.poll_interval_secs = poll_interval_secs
        self.expires_after_days = expires_after_days
        
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable required")
            
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            organization=None,
            project=self.project_id
        )
        
        # Track created resources for cleanup
        self.vector_store_id = None
        self.assistant_id = None
        self.thread_id = None
        self.uploaded_file_ids = []
        self.temp_dirs = []
        
        logger.info(f"EditingTeam initialized with project: {self.project_id}, model: {self.model}")
    
    def synthesize_chapter(self, research_notes: dict[str, Any]) -> ChapterDraft:
        """
        Main interface method for US-004: synthesize chapter content using Response API file_search.
        
        Multi-step synthesis approach:
        1. Combine syllabus + agenda + research notes
        2. Use Response API file_search for content generation
        3. Apply training course narrative guidelines
        4. Agent-to-agent feedback loops within editing team
        
        Args:
            research_notes: Research notes data structure containing:
                - syllabus: Course syllabus information
                - agenda: Module agenda details  
                - research_notes: Detailed research findings per module
                - target_section: Section to synthesize
        
        Returns:
            ChapterDraft: Synthesized chapter content
        """
        try:
            target_section = research_notes.get('target_section', 'Unknown Section')
            logger.info(f"Starting chapter synthesis for section: {target_section}")
            
            # Step 1: Create research files for file_search
            logger.info("Step 1: Creating research files for file_search")
            file_paths = self._create_research_files(research_notes)
            
            # Step 2: Upload files and create vector store
            logger.info("Step 2: Uploading files and creating vector store")
            vector_store_id = self._upload_files_for_search(file_paths)
            
            # Step 3: Create research assistant with file_search capability
            logger.info("Step 3: Creating research assistant")
            assistant_id = self._create_research_assistant(vector_store_id)
            
            # Step 4: Multi-step content synthesis
            logger.info("Step 4: Executing multi-step content synthesis")
            synthesized_content = self._execute_synthesis_workflow(research_notes, assistant_id)
            
            # Step 5: Create final chapter draft
            chapter_draft = ChapterDraft(
                section_id=target_section,
                content=synthesized_content
            )
            
            logger.info(f"Chapter synthesis completed for section: {target_section}")
            return chapter_draft
            
        except Exception as e:
            logger.error(f"Chapter synthesis failed for section {target_section}: {e!s}")
            # Return empty chapter draft on failure
            return ChapterDraft(
                section_id=research_notes.get('target_section', 'Unknown Section'),
                content=f"Error: Unable to synthesize content. {e!s}"
            )
        finally:
            # Clean up resources
            self._cleanup_resources()
    
    def _create_research_files(self, research_notes: dict[str, Any]) -> list[str]:
        """Create temporary files from research data for file_search upload"""
        file_paths = []
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            # Create syllabus file
            syllabus_path = os.path.join(temp_dir, "course_syllabus.md")
            with open(syllabus_path, 'w', encoding='utf-8') as f:
                f.write("# Course Syllabus\n\n")
                syllabus = research_notes.get('syllabus', {})
                f.write(f"**Course:** {syllabus.get('title', 'N/A')}\n")
                f.write(f"**Duration:** {syllabus.get('duration_weeks', 'N/A')} weeks\n\n")
                f.write("## Learning Objectives\n")
                for obj in syllabus.get('learning_objectives', []):
                    f.write(f"- {obj}\n")
                f.write("\n## Key Topics\n")
                for topic in syllabus.get('key_topics', []):
                    f.write(f"- {topic}\n")
            file_paths.append(syllabus_path)
            
            # Create agenda file
            agenda_path = os.path.join(temp_dir, "module_agenda.md")
            with open(agenda_path, 'w', encoding='utf-8') as f:
                f.write("# Module Agenda\n\n")
                agenda = research_notes.get('agenda', [])
                for i, module in enumerate(agenda, 1):
                    if isinstance(module, dict):
                        f.write(f"## Module {i}: {module.get('title', 'Untitled')}\n")
                        f.write(f"**Duration:** {module.get('duration_minutes', 'N/A')} minutes\n")
                        f.write("### Topics:\n")
                        for topic in module.get('topics', []):
                            f.write(f"- {topic}\n")
                        f.write("\n")
                    else:
                        f.write(f"## Module {i}: {module}\n\n")
            file_paths.append(agenda_path)
            
            # Create research notes files
            notes = research_notes.get('research_notes', {})
            for module_name, note_content in notes.items():
                notes_path = os.path.join(temp_dir, f"research_notes_{module_name.replace(' ', '_').lower()}.md")
                with open(notes_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Research Notes: {module_name}\n\n")
                    if isinstance(note_content, dict):
                        for section, content in note_content.items():
                            f.write(f"## {section}\n\n{content}\n\n")
                    else:
                        f.write(f"{note_content}\n")
                file_paths.append(notes_path)
            
            # Create training guidelines file
            guidelines_path = os.path.join(temp_dir, "training_guidelines.md")
            with open(guidelines_path, 'w', encoding='utf-8') as f:
                f.write(self._get_training_guidelines())
            file_paths.append(guidelines_path)
                
            logger.info(f"Created {len(file_paths)} research files in {temp_dir}")
            return file_paths
            
        except Exception as e:
            logger.error(f"Error creating research files: {e!s}")
            # Cleanup on error
            try:
                shutil.rmtree(temp_dir)
                if temp_dir in self.temp_dirs:
                    self.temp_dirs.remove(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {cleanup_error}")
            raise
    
    def _upload_files_for_search(self, file_paths: list[str]) -> str:
        """Upload files to OpenAI and create vector store for file_search"""
        try:
            # Upload files
            uploaded_files = []
            for file_path in file_paths:
                logger.info(f"Uploading {os.path.basename(file_path)}...")
                with open(file_path, 'rb') as file:
                    uploaded_file = self.client.files.create(
                        file=file,
                        purpose='assistants'
                    )
                    uploaded_files.append(uploaded_file)
                    self.uploaded_file_ids.append(uploaded_file.id)
                    
            logger.info(f"Uploaded {len(uploaded_files)} files successfully")
            
            # Create vector store
            vector_store = self.client.beta.vector_stores.create(
                name="EditingTeam Research Vector Store",
                expires_after={
                    "anchor": "last_active_at",
                    "days": self.expires_after_days
                }
            )
            self.vector_store_id = vector_store.id
            logger.info(f"Created vector store: {vector_store.id}")
            
            # Add files to vector store with batch upload
            file_batch = self.client.beta.vector_stores.file_batches.create_and_poll(
                vector_store_id=vector_store.id,
                file_ids=[f.id for f in uploaded_files]
            )
            logger.info(f"File batch processed with status: {file_batch.status}")
            
            return vector_store.id
            
        except Exception as e:
            logger.error(f"File upload failed: {e!s}")
            raise
    
    def _create_research_assistant(self, vector_store_id: str) -> str:
        """Create research assistant with file_search tool"""
        try:
            assistant = self.client.beta.assistants.create(
                name="EditingTeam Content Synthesizer",
                description="Multi-agent editing team for training course content synthesis",
                model=self.model,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                },
                instructions=self._get_assistant_instructions()
            )
            self.assistant_id = assistant.id
            logger.info(f"Created research assistant: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            logger.error(f"Assistant creation failed: {e!s}")
            raise
    
    def _execute_synthesis_workflow(self, research_notes: dict[str, Any], assistant_id: str) -> str:
        """Execute multi-step content synthesis workflow with agent feedback loops"""
        try:
            target_section = research_notes.get('target_section', 'Unknown Section')
            
            # Create thread for conversation
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            
            # Step 1: Documentalist - Extract and organize content
            documentalist_query = self._create_documentalist_query(target_section, research_notes)
            documented_content = self._synthesize_content_step(thread.id, assistant_id, documentalist_query, "documentalist")
            
            # Step 2: Writer - Draft chapter content
            writer_query = self._create_writer_query(target_section, documented_content, research_notes)
            draft_content = self._synthesize_content_step(thread.id, assistant_id, writer_query, "writer")
            
            # Step 3: Reviewer - Review and provide feedback
            reviewer_query = self._create_reviewer_query(target_section, draft_content)
            review_feedback = self._synthesize_content_step(thread.id, assistant_id, reviewer_query, "reviewer")
            
            # Step 4: Script Strategist - Final revision based on feedback
            final_query = self._create_final_revision_query(target_section, draft_content, review_feedback)
            final_content = self._synthesize_content_step(thread.id, assistant_id, final_query, "script_strategist")
            
            logger.info(f"Multi-step synthesis completed for section: {target_section}")
            return final_content
            
        except Exception as e:
            logger.error(f"Synthesis workflow failed: {e!s}")
            raise
    
    def _synthesize_content_step(self, thread_id: str, assistant_id: str, query: str, agent_role: str) -> str:
        """Execute single synthesis step with specific agent role"""
        try:
            logger.info(f"Executing {agent_role} synthesis step")
            
            # Create message
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=query
            )
            
            # Create and run assistant
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            if run.status == 'completed':
                # Get response messages
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.data:
                    content = messages.data[0].content[0].text.value
                    logger.info(f"{agent_role} synthesis step completed successfully")
                    return content
                else:
                    logger.warning(f"No response from {agent_role} synthesis")
                    return f"No response generated for {agent_role} step"
            else:
                error_msg = f"Run failed with status: {run.status}"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg += f", Error: {run.last_error}"
                logger.error(f"{agent_role} synthesis failed: {error_msg}")
                return f"Error in {agent_role} synthesis: {error_msg}"
                
        except Exception as e:
            logger.error(f"{agent_role} synthesis step failed: {e!s}")
            return f"Error in {agent_role} synthesis: {e!s}"
    
    def _create_documentalist_query(self, target_section: str, research_notes: dict[str, Any]) -> str:
        """Create query for Documentalist agent"""
        return f"""As the Documentalist in our editing team, your role is to extract and organize relevant content from the research materials for the section "{target_section}".

Your tasks:
1. Search through the syllabus, agenda, and research notes to find all content related to "{target_section}"
2. Identify key learning objectives and topics that must be covered
3. Extract relevant examples, case studies, and supporting materials
4. Organize the information in a logical structure for content creation
5. Note any gaps or areas that need additional research

Please provide a comprehensive documented summary that will guide the Writer in creating effective training content."""
    
    def _create_writer_query(self, target_section: str, documented_content: str, research_notes: dict[str, Any]) -> str:
        """Create query for Writer agent"""
        return f"""As the Writer in our editing team, create engaging training content for the section "{target_section}" based on the Documentalist's research summary.

Documentalist's Summary:
{documented_content}

Your tasks:
1. Write compelling and pedagogically sound content following training course guidelines
2. Apply learning scaffolding, active learning, and knowledge anchoring patterns
3. Use a conversational tone with contextual hooks and narrative flow
4. Include thought questions and interactive prompts for learners
5. Ensure content aligns with syllabus objectives and agenda topics
6. Structure content with clear sections, examples, and practical applications

Create a complete chapter draft that is ready for review."""
    
    def _create_reviewer_query(self, target_section: str, draft_content: str) -> str:
        """Create query for Reviewer agent"""
        return f"""As the Reviewer in our editing team, evaluate the draft content for section "{target_section}" and provide constructive feedback.

Draft Content:
{draft_content}

Your evaluation criteria:
1. Pedagogical effectiveness - Does it follow learning scaffolding and active learning principles?
2. Content accuracy - Is the information correct and up-to-date?
3. Engagement level - Will learners find this interesting and motivating?
4. Structure and flow - Is the content well-organized with smooth transitions?
5. Alignment with objectives - Does it meet the stated learning goals?
6. Clarity and accessibility - Is the language appropriate for the target audience?

Provide specific feedback on what works well and what needs improvement. Include suggestions for enhancing content quality."""
    
    def _create_final_revision_query(self, target_section: str, draft_content: str, review_feedback: str) -> str:
        """Create query for Script Strategist final revision"""
        return f"""As the Script Strategist in our editing team, create the final polished version of the content for section "{target_section}" incorporating the Reviewer's feedback.

Original Draft:
{draft_content}

Reviewer Feedback:
{review_feedback}

Your tasks:
1. Address all concerns raised by the Reviewer
2. Enhance content quality while maintaining the core message
3. Ensure excellent narrative flow and learner engagement
4. Optimize the content structure for maximum learning impact
5. Add any missing elements that would improve the training experience
6. Create a final version that is production-ready

Deliver a polished, comprehensive chapter that exemplifies best practices in training content creation."""
    
    def _get_assistant_instructions(self) -> str:
        """Get comprehensive instructions for the assistant"""
        return """You are a member of an elite EditingTeam specializing in training course content synthesis. You work collaboratively with other agents (Documentalist, Writer, Reviewer, Script Strategist) to create exceptional educational content.

Key Principles:
1. Use file_search to find relevant information from uploaded research materials
2. Apply training course narrative guidelines for pedagogical effectiveness
3. Maintain high standards for content quality and learner engagement
4. Collaborate effectively with other team members by building on their work
5. Ensure all content aligns with syllabus objectives and learning goals

When responding:
- Always search the research materials thoroughly using file_search
- Reference specific sources and examples from the materials
- Apply pedagogical best practices (scaffolding, active learning, knowledge anchoring)
- Use engaging, conversational tone appropriate for training content
- Structure responses clearly with appropriate headings and formatting
- Include practical examples and interactive elements where appropriate"""
    
    def _get_training_guidelines(self) -> str:
        """Get training course guidelines content"""
        guidelines_path = Path(__file__).parent.parent / "guidelines" / "training_course_guidelines.md"
        try:
            with open(guidelines_path, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Training guidelines file not found at {guidelines_path}")
            return """# Training Course Guidelines

## Pedagogical Patterns
1. Learning Scaffolding - Build upon prior knowledge gradually
2. Active Learning - Include interactive elements and questions
3. Knowledge Anchoring - Use real-world examples and analogies
4. Engagement Patterns - Maintain interest with varied content

## Key Principles
- Use conversational tone
- Include thought-provoking questions
- Provide practical examples
- Ensure smooth content flow"""
    
    def _cleanup_resources(self):
        """Clean up OpenAI resources and temporary files"""
        try:
            # Delete vector store
            if self.vector_store_id:
                try:
                    self.client.beta.vector_stores.delete(self.vector_store_id)
                    logger.info(f"Deleted vector store: {self.vector_store_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete vector store {self.vector_store_id}: {e}")
                self.vector_store_id = None
            
            # Delete assistant
            if self.assistant_id:
                try:
                    self.client.beta.assistants.delete(self.assistant_id)
                    logger.info(f"Deleted assistant: {self.assistant_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete assistant {self.assistant_id}: {e}")
                self.assistant_id = None
            
            # Delete uploaded files
            for file_id in self.uploaded_file_ids:
                try:
                    self.client.files.delete(file_id)
                    logger.info(f"Deleted file: {file_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_id}: {e}")
            self.uploaded_file_ids.clear()
            
            # Clean up temporary directories
            for temp_dir in self.temp_dirs:
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
            self.temp_dirs.clear()
            
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e!s}")


# Legacy function for backward compatibility
def edit_chapters(research_notes, config):
    """
    Legacy function for backward compatibility with existing code.
    For each module, produce a draft script using the new EditingTeam class.
    """
    logger.info("Using legacy edit_chapters interface with EditingTeam implementation")
    
    try:
        editing_team = EditingTeam(
            max_revisions=config.get('max_revisions', 2)
        )
        
        drafts: dict[str, str] = {}
        for module, note in research_notes.items():
            if not note.strip():
                logger.error(f"No research notes provided for module: {module}")
                raise RuntimeError(f"[editing_team] No research notes provided for module: {module}. Aborting edit.")
            
            # Convert legacy format to new format
            research_data = {
                'target_section': module,
                'syllabus': {
                    'title': 'Legacy Course',
                    'duration_weeks': 'N/A',
                    'learning_objectives': [],
                    'key_topics': []
                },
                'agenda': [{'title': module, 'topics': []}],
                'research_notes': {module: note}
            }
            
            # Synthesize chapter
            chapter_draft = editing_team.synthesize_chapter(research_data)
            drafts[module] = chapter_draft.content
            
        logger.info(f"Completed editing for {len(drafts)} modules")
        return drafts
        
    except Exception as e:
        logger.error(f"Legacy edit_chapters failed: {e!s}")
        # Fallback to stub behavior
        logger.warning("Falling back to stub implementation")
        drafts: dict[str, str] = {}
        for module, note in research_notes.items():
            if not note.strip():
                raise RuntimeError(f"[editing_team] No research notes provided for module: {module}. Aborting edit.")
            drafts[module] = note
        return drafts