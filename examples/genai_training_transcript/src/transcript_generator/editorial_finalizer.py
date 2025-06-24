"""
Editorial Finalizer - Quality Control and Misconduct Tracking

This module implements US-005: Editorial Finalizer Misconduct Tracking
Module: transcript_generator/editorial_finalizer.py
Interface: EditorialFinalizer class with finalize_content(chapters), track_issues() methods

Acceptance Criteria:
- EditorialFinalizer outputs final_transcript.md + quality_issues.json with misconduct tracking
- Integration Point: Consumes chapter_drafts/, exports quality metadata for evaluation module
- Reviews generated content for quality issues and narrative consistency
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Import centralized environment configuration
from ..common.environment import env_config

# Import multi-agent implementation (direct import - dependency in poetry.lock)
from .editorial_finalizer_multi_agent import MultiAgentEditorialFinalizer

class IssueSeverity(Enum):
    """Issue severity levels for misconduct tracking"""
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"

@dataclass
class QualityIssue:
    """Represents a quality issue detected in content"""
    description: str
    severity: IssueSeverity
    section_id: str | None = None
    misconduct_category: str | None = None

@dataclass
class ChapterDraft:
    """Chapter draft data structure"""
    section_id: str
    content: str
    title: str | None = None

@dataclass
class QualityIssues:
    """Quality issues data structure for JSON export"""
    section_id: str
    issues: list[dict[str, str]]
    approved: bool

@dataclass
class FinalTranscript:
    """Final transcript data structure"""
    course_title: str
    sections: list[dict[str, str]]

class EditorialFinalizer:
    """
    Editorial Finalizer for quality control and misconduct tracking.
    
    This class implements the final quality control step in the content generation pipeline.
    It analyzes chapter drafts for various types of misconduct and issues, then produces
    both a final transcript and detailed quality tracking information.
    
    Misconduct Categories (as defined in US-005 specifications):
    - CRITICAL: content_syllabus_alignment, inadequate_level
    - HIGH: duration_violations, groundedness_violations, training_principles_violations  
    - MEDIUM: content_repetition
    """
    
    def __init__(self, 
                 output_dir: str = "output", 
                 quality_dir: str = "quality_issues",
                 enable_multi_agent: bool = True,
                 model: str = "gpt-4o-mini"):
        """
        Initialize the Editorial Finalizer.
        
        Args:
            output_dir: Directory to write final transcript
            quality_dir: Directory to write quality issues JSON files
            enable_multi_agent: Use sophisticated multi-agent assessment if available
            model: Model to use for multi-agent assessment
        """
        # Always delegate to multi-agent implementation  
        if enable_multi_agent:
            self._delegate = MultiAgentEditorialFinalizer(
                output_dir=output_dir,
                quality_dir=quality_dir, 
                enable_multi_agent=enable_multi_agent,
                model=model
            )
            self._using_multi_agent = True
        else:
            self._delegate = None
            self._using_multi_agent = False
            
            # Initialize basic implementation
            self.output_dir = Path(output_dir)
            self.quality_dir = Path(quality_dir)
            self.output_dir.mkdir(exist_ok=True)
            self.quality_dir.mkdir(exist_ok=True)
            
            # Setup logging
            self.logger = logging.getLogger(__name__)
            self.logger.info("Multi-agent assessment disabled by configuration")
        
        # Quality thresholds - configurable for different content types
        self.quality_thresholds = {
            'min_word_count': 50,
            'max_word_count': 2000,
            'min_vocabulary_ratio': 0.4,
            'error_penalty': 0.3,
            'warning_penalty': 0.1,
            'min_structure_score': 2,
            'min_engagement_threshold': 300
        }
        
        # Misconduct categories as defined in specifications
        self.misconduct_categories = {
            "CRITICAL": [
                "content_syllabus_alignment",  # missing modules, off-topic content
                "inadequate_level"  # content too difficult/simple for target audience
            ],
            "HIGH": [
                "duration_violations",  # generated content timing vs syllabus requirements
                "groundedness_violations",  # content not based on provided knowledge base
                "training_principles_violations"  # tone, style, structure
            ],
            "MEDIUM": [
                "content_repetition"  # topics addressed twice without new angle
            ]
        }

    def finalize_content(self, chapters: list[ChapterDraft], syllabus: dict[str, Any] | None = None) -> tuple[str, str]:
        """
        Finalize content by reviewing chapters and producing final transcript.
        
        Automatically uses sophisticated multi-agent assessment when available,
        falling back to basic pattern matching when necessary.
        
        Args:
            chapters: List of chapter drafts to review and finalize
            syllabus: Optional syllabus for alignment checking
            
        Returns:
            Tuple of (final_transcript_path, quality_summary_path)
        """
        # Delegate to multi-agent implementation if available
        if self._using_multi_agent:
            return self._delegate.finalize_content(chapters, syllabus)
        
        # Continue with basic implementation
        self.logger.info(f"Starting content finalization for {len(chapters)} chapters")
        
        # Track all quality issues across chapters
        all_quality_issues = []
        final_sections = []
        
        # Process each chapter
        for chapter in chapters:
            self.logger.info(f"Processing chapter: {chapter.section_id}")
            
            # Detect quality issues using track_issues method
            quality_issues = self.track_issues(chapter, syllabus)
            all_quality_issues.extend(quality_issues)
            
            # Create quality issues file for this section (per schema)
            section_quality = {
                "section_id": chapter.section_id,
                "issues": [{
                    "description": issue.description,
                    "severity": issue.severity.value
                } for issue in quality_issues],
                "approved": not any(issue.severity == IssueSeverity.ERROR for issue in quality_issues)
            }
            
            # Write quality issues for this section to quality_issues/{section_id}.json
            quality_file = self.quality_dir / f"{chapter.section_id}.json"
            try:
                with open(quality_file, 'w', encoding='utf-8') as f:
                    json.dump(section_quality, f, indent=2, ensure_ascii=False)
            except OSError as e:
                self.logger.error(f"Failed to write quality file {quality_file}: {e}")
                raise
            
            # Add to final transcript (regardless of issues - flagged in quality_issues)
            final_sections.append({
                "section_id": chapter.section_id,
                "title": chapter.title or f"Section {chapter.section_id}",
                "content": chapter.content
            })
        
        # Create final transcript according to schema
        final_transcript = {
            "course_title": syllabus.get("course_title", "Generated Training Course") if syllabus else "Generated Training Course",
            "sections": final_sections
        }
        
        # Write final transcript JSON
        transcript_json_path = self.output_dir / "final_transcript.json"
        try:
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(final_transcript, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.logger.error(f"Failed to write final transcript {transcript_json_path}: {e}")
            raise
        
        # Create markdown version for readability
        md_path = self.output_dir / "final_transcript.md"
        self._create_markdown_transcript(final_transcript, md_path)
        
        # Create summary quality report
        summary_path = self.quality_dir / "quality_summary.json"
        self._create_quality_summary(all_quality_issues, summary_path)
        
        self.logger.info(f"Content finalization complete. Transcript: {md_path}, Quality: {summary_path}")
        return str(md_path), str(summary_path)

    def track_issues(self, chapter: ChapterDraft, syllabus: dict[str, Any] | None = None) -> list[QualityIssue]:
        """
        Track quality issues and misconduct in a chapter draft.
        
        Automatically uses sophisticated multi-agent assessment when available,
        falling back to basic pattern matching when necessary.
        
        Args:
            chapter: Chapter draft to analyze
            syllabus: Optional syllabus for alignment checking
            
        Returns:
            List of detected quality issues with severity and misconduct category
        """
        # Delegate to multi-agent implementation if available
        if self._using_multi_agent:
            return self._delegate.track_issues(chapter, syllabus)
        
        # Continue with basic pattern matching implementation
        issues = []
        
        # Basic content validation
        if not chapter.content or len(chapter.content.strip()) < 100:
            issues.append(QualityIssue(
                description="Chapter content is too short (less than 100 characters)",
                severity=IssueSeverity.ERROR,
                section_id=chapter.section_id,
                misconduct_category="inadequate_level"
            ))
        
        # Check for syllabus alignment if provided (CRITICAL category)
        if syllabus:
            issues.extend(self._check_syllabus_alignment(chapter, syllabus))
        
        # Check for content quality issues (MEDIUM category)
        issues.extend(self._check_content_quality(chapter))
        
        # Check for training course principles (HIGH category)
        issues.extend(self._check_training_principles(chapter))
        
        # Check for groundedness violations (HIGH category)
        issues.extend(self._check_groundedness(chapter))
        
        return issues

    def _check_syllabus_alignment(self, chapter: ChapterDraft, syllabus: dict[str, Any]) -> list[QualityIssue]:
        """Check if chapter content aligns with syllabus requirements (CRITICAL misconduct)"""
        issues = []
        
        # Find corresponding syllabus section
        syllabus_section = None
        if "sections" in syllabus:
            for section in syllabus["sections"]:
                if section.get("section_id") == chapter.section_id:
                    syllabus_section = section
                    break
        
        if not syllabus_section:
            issues.append(QualityIssue(
                description=f"No corresponding syllabus section found for {chapter.section_id}",
                severity=IssueSeverity.ERROR,
                section_id=chapter.section_id,
                misconduct_category="content_syllabus_alignment"
            ))
            return issues
        
        # Check if learning objectives are addressed
        learning_objectives = syllabus_section.get("learning_objectives", [])
        content_lower = chapter.content.lower()
        
        missing_objectives = []
        for objective in learning_objectives:
            # Simple keyword matching - in production would use more sophisticated NLP
            objective_keywords = objective.lower().split()[:3]  # First 3 words as approximation
            if not any(keyword in content_lower for keyword in objective_keywords):
                missing_objectives.append(objective)
        
        if missing_objectives:
            issues.append(QualityIssue(
                description=f"Learning objectives not clearly addressed: {', '.join(missing_objectives[:2])}{'...' if len(missing_objectives) > 2 else ''}",
                severity=IssueSeverity.WARNING,
                section_id=chapter.section_id,
                misconduct_category="content_syllabus_alignment"
            ))
        
        # Check key topics coverage
        key_topics = syllabus_section.get("key_topics", [])
        missing_topics = []
        for topic in key_topics:
            topic_lower = topic.lower()
            if topic_lower not in content_lower:
                missing_topics.append(topic)
        
        if missing_topics and len(missing_topics) > len(key_topics) / 2:  # More than half missing
            issues.append(QualityIssue(
                description=f"Key topics not adequately covered: {', '.join(missing_topics[:3])}{'...' if len(missing_topics) > 3 else ''}",
                severity=IssueSeverity.WARNING,
                section_id=chapter.section_id,
                misconduct_category="content_syllabus_alignment"
            ))
        
        return issues

    def _check_content_quality(self, chapter: ChapterDraft) -> list[QualityIssue]:
        """Check for general content quality issues (MEDIUM misconduct)"""
        issues = []
        content = chapter.content
        
        # Check for repetitive content (simple word frequency analysis)
        words = content.lower().split()
        word_count = len(words)
        unique_words = len(set(words))
        
        if word_count > 100 and unique_words / word_count < self.quality_thresholds['min_vocabulary_ratio']:
            issues.append(QualityIssue(
                description="Content appears repetitive with low vocabulary diversity",
                severity=IssueSeverity.WARNING,
                section_id=chapter.section_id,
                misconduct_category="content_repetition"
            ))
        
        # Check for extremely short content (inadequate level)
        if word_count < self.quality_thresholds['min_word_count']:
            issues.append(QualityIssue(
                description=f"Content is too short ({word_count} words)",
                severity=IssueSeverity.ERROR,
                section_id=chapter.section_id,
                misconduct_category="inadequate_level"
            ))
        elif word_count > self.quality_thresholds['max_word_count']:
            # Duration violations - content too long
            issues.append(QualityIssue(
                description=f"Content may be too long ({word_count} words) for a single section",
                severity=IssueSeverity.INFO,
                section_id=chapter.section_id,
                misconduct_category="duration_violations"
            ))
        
        # Check for placeholder text or obvious AI artifacts
        ai_indicators = [
            "as an ai", "i am an ai", "i cannot", "i don't have access",
            "[placeholder]", "todo:", "fixme:", "lorem ipsum"
        ]
        
        content_lower = content.lower()
        for indicator in ai_indicators:
            if indicator in content_lower:
                issues.append(QualityIssue(
                    description=f"Content contains AI artifacts or placeholder text: '{indicator}'",
                    severity=IssueSeverity.ERROR,
                    section_id=chapter.section_id,
                    misconduct_category="training_principles_violations"
                ))
        
        return issues

    def _check_training_principles(self, chapter: ChapterDraft) -> list[QualityIssue]:
        """Check adherence to training course principles (HIGH misconduct)"""
        issues = []
        content = chapter.content
        
        # Check for educational structure elements
        has_intro = any(word in content.lower() for word in ['introduction', 'overview', 'begin', 'start', 'welcome'])
        has_examples = any(word in content.lower() for word in ['example', 'for instance', 'such as', 'consider'])
        has_summary = any(word in content.lower() for word in ['summary', 'conclusion', 'recap', 'key points'])
        
        structure_score = sum([has_intro, has_examples, has_summary])
        
        if structure_score < self.quality_thresholds['min_structure_score'] and len(content.split()) > 200:
            issues.append(QualityIssue(
                description="Content lacks clear educational structure (introduction, examples, summary)",
                severity=IssueSeverity.WARNING,
                section_id=chapter.section_id,
                misconduct_category="training_principles_violations"
            ))
        
        # Check for engagement elements
        engagement_elements = [
            '?',  # Questions
            'exercise', 'practice', 'try', 'activity', 'hands-on'
        ]
        
        engagement_count = sum(1 for element in engagement_elements if element in content.lower())
        
        if engagement_count == 0 and len(content.split()) > self.quality_thresholds['min_engagement_threshold']:
            issues.append(QualityIssue(
                description="Content lacks engagement elements (questions, exercises, interactive components)",
                severity=IssueSeverity.INFO,
                section_id=chapter.section_id,
                misconduct_category="training_principles_violations"
            ))
        
        return issues

    def _check_groundedness(self, chapter: ChapterDraft) -> list[QualityIssue]:
        """Check for groundedness violations (HIGH misconduct)"""
        issues = []
        content = chapter.content
        
        # Check for vague or unsupported claims
        vague_indicators = [
            "it is known that", "everyone knows", "obviously", "clearly",
            "without a doubt", "it goes without saying"
        ]
        
        content_lower = content.lower()
        for indicator in vague_indicators:
            if indicator in content_lower:
                issues.append(QualityIssue(
                    description=f"Content contains unsupported claims: '{indicator}'",
                    severity=IssueSeverity.WARNING,
                    section_id=chapter.section_id,
                    misconduct_category="groundedness_violations"
                ))
        
        # Check for lack of specific examples or evidence
        if len(content.split()) > 300:  # Only for substantial content
            has_specifics = any(word in content_lower for word in [
                'according to', 'research shows', 'study', 'data', 'statistics',
                'for example', 'specifically', 'in particular'
            ])
            
            if not has_specifics:
                issues.append(QualityIssue(
                    description="Content lacks specific examples or evidence to support claims",
                    severity=IssueSeverity.INFO,
                    section_id=chapter.section_id,
                    misconduct_category="groundedness_violations"
                ))
        
        return issues

    def _create_markdown_transcript(self, transcript: dict[str, Any], output_path: Path):
        """Create markdown version of final transcript"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {transcript['course_title']}\n\n")
            
            for section in transcript['sections']:
                f.write(f"## {section['title']}\n\n")
                f.write(f"{section['content']}\n\n")
                f.write("---\n\n")

    def _create_quality_summary(self, all_issues: list[QualityIssue], output_path: Path):
        """Create summary quality report for evaluation system integration"""
        summary = {
            "total_issues": len(all_issues),
            "issues_by_severity": {
                "INFO": len([i for i in all_issues if i.severity == IssueSeverity.INFO]),
                "WARNING": len([i for i in all_issues if i.severity == IssueSeverity.WARNING]),
                "ERROR": len([i for i in all_issues if i.severity == IssueSeverity.ERROR])
            },
            "issues_by_category": {},
            "sections_with_errors": list(set(i.section_id for i in all_issues if i.severity == IssueSeverity.ERROR and i.section_id)),
            "details": [
                {
                    "section_id": issue.section_id,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "category": issue.misconduct_category
                }
                for issue in all_issues
            ]
        }
        
        # Count by misconduct category
        for issue in all_issues:
            if issue.misconduct_category:
                summary["issues_by_category"][issue.misconduct_category] = \
                    summary["issues_by_category"].get(issue.misconduct_category, 0) + 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def get_quality_metrics(self) -> dict[str, Any]:
        """
        Get quality metrics for evaluation system integration.
        
        Automatically uses enhanced multi-agent metrics when available,
        falling back to basic metrics when necessary.
        
        Returns:
            Dictionary containing quality metrics for LangSmith logging
        """
        # Delegate to multi-agent implementation if available
        if self._using_multi_agent:
            return self._delegate.get_quality_metrics()
        
        # Continue with basic metrics implementation
        # Read quality summary if it exists
        summary_path = self.quality_dir / "quality_summary.json"
        if summary_path.exists():
            with open(summary_path, encoding='utf-8') as f:
                summary = json.load(f)
            
            return {
                "total_issues": summary.get("total_issues", 0),
                "error_count": summary.get("issues_by_severity", {}).get("ERROR", 0),
                "warning_count": summary.get("issues_by_severity", {}).get("WARNING", 0),
                "sections_with_errors": len(summary.get("sections_with_errors", [])),
                "misconduct_categories": summary.get("issues_by_category", {}),
                "quality_score": self._calculate_quality_score(summary)
            }
        
        # Basic fallback metrics
        return {
            "total_issues": 0, 
            "error_count": 0, 
            "warning_count": 0, 
            "sections_with_errors": 0,
            "misconduct_categories": {},
            "quality_score": 1.0,
            "assessment_type": "basic_pattern_matching"
        }

    def _calculate_quality_score(self, summary: dict[str, Any]) -> float:
        """Calculate overall quality score (0-1) for evaluation metrics"""
        total_issues = summary.get("total_issues", 0)
        error_count = summary.get("issues_by_severity", {}).get("ERROR", 0)
        warning_count = summary.get("issues_by_severity", {}).get("WARNING", 0)
        
        if total_issues == 0:
            return 1.0
        
        # Weighted scoring: errors more impactful than warnings
        penalty = (error_count * self.quality_thresholds['error_penalty']) + (warning_count * self.quality_thresholds['warning_penalty'])
        score = max(0.0, 1.0 - penalty)
        
        return round(score, 2) 