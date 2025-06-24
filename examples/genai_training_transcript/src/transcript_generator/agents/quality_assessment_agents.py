"""
Multi-Agent Quality Assessment System for EditorialFinalizer

This module implements sophisticated multi-agent quality assessment using OpenAI Agents SDK
to replace the basic pattern matching approach in the EditorialFinalizer.

Architecture:
- SemanticAlignmentAgent: Verifies content-syllabus semantic alignment
- PedagogicalQualityAgent: Assesses pedagogical effectiveness and learning design
- GroundednessAgent: Evaluates content groundedness and evidence quality
- ContentDepthAgent: Analyzes content complexity and appropriateness
- GuidelinesComplianceAgent: Checks training course guidelines adherence
- QualityConsensusOrchestrator: Coordinates agents and builds consensus

Each agent specializes in specific quality dimensions and provides structured assessments
that are combined into comprehensive quality reports.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Import centralized environment configuration
from ...common.environment import env_config

# Import Agents SDK directly - dependencies are in poetry.lock
from agents import Agent, Runner

logger = logging.getLogger(__name__)


class AssessmentConfidence(Enum):
    """Confidence levels for agent assessments"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class QualityDimension(Enum):
    """Quality dimensions assessed by different agents"""
    SEMANTIC_ALIGNMENT = "semantic_alignment"
    PEDAGOGICAL_QUALITY = "pedagogical_quality"
    GROUNDEDNESS = "groundedness"
    CONTENT_DEPTH = "content_depth"
    GUIDELINES_COMPLIANCE = "guidelines_compliance"


@dataclass
class ChapterContent:
    """Chapter content data for agent assessment"""
    section_id: str
    title: str
    content: str
    syllabus_section: dict[str, Any] | None = None


@dataclass
class QualityFinding:
    """Individual quality finding from an agent"""
    description: str
    severity: str  # "INFO", "WARNING", "ERROR"
    confidence: AssessmentConfidence
    category: str
    evidence: list[str]
    recommendations: list[str]


class AgentAssessment(BaseModel):
    """Structured assessment output from quality agents"""
    dimension: str = Field(description="Quality dimension being assessed")
    overall_score: float = Field(description="Overall quality score (0-1)", ge=0, le=1)
    confidence: str = Field(description="Confidence level of assessment")
    findings: list[dict[str, Any]] = Field(description="Specific quality findings")
    recommendations: list[str] = Field(description="Improvement recommendations")
    evidence_summary: str = Field(description="Summary of evidence considered")


class SemanticAlignmentAssessment(BaseModel):
    """Semantic alignment specific assessment"""
    content_topic_match: float = Field(description="How well content matches expected topic (0-1)")
    learning_objectives_coverage: float = Field(description="Coverage of learning objectives (0-1)")
    key_topics_alignment: float = Field(description="Alignment with key topics (0-1)")
    difficulty_level_match: float = Field(description="Appropriateness of difficulty level (0-1)")
    semantic_coherence: float = Field(description="Semantic coherence and focus (0-1)")
    misalignment_details: list[str] = Field(description="Specific misalignment issues identified")


class PedagogicalAssessment(BaseModel):
    """Pedagogical quality specific assessment"""
    learning_scaffolding: float = Field(description="Quality of learning scaffolding (0-1)")
    knowledge_anchoring: float = Field(description="Effectiveness of knowledge anchoring (0-1)")
    engagement_elements: float = Field(description="Presence and quality of engagement elements (0-1)")
    active_learning: float = Field(description="Active learning opportunities (0-1)")
    instructional_design: float = Field(description="Overall instructional design quality (0-1)")
    pedagogical_gaps: list[str] = Field(description="Identified pedagogical gaps")


class GroundednessAssessment(BaseModel):
    """Groundedness specific assessment"""
    evidence_quality: float = Field(description="Quality of evidence and support (0-1)")
    claim_substantiation: float = Field(description="How well claims are substantiated (0-1)")
    factual_accuracy: float = Field(description="Apparent factual accuracy (0-1)")
    source_attribution: float = Field(description="Quality of source attribution (0-1)")
    unsupported_claims: list[str] = Field(description="Identified unsupported claims")


class ContentDepthAssessment(BaseModel):
    """Content depth specific assessment"""
    complexity_appropriateness: float = Field(description="Appropriateness of complexity level (0-1)")
    conceptual_depth: float = Field(description="Depth of conceptual coverage (0-1)")
    technical_rigor: float = Field(description="Technical rigor and precision (0-1)")
    audience_alignment: float = Field(description="Alignment with target audience (0-1)")
    depth_issues: list[str] = Field(description="Specific depth-related issues")


class GuidelinesComplianceAssessment(BaseModel):
    """Guidelines compliance specific assessment"""
    structure_compliance: float = Field(description="Compliance with structural guidelines (0-1)")
    tone_appropriateness: float = Field(description="Appropriateness of tone and style (0-1)")
    pacing_quality: float = Field(description="Quality of content pacing (0-1)")
    accessibility: float = Field(description="Content accessibility and clarity (0-1)")
    compliance_violations: list[str] = Field(description="Identified compliance violations")


class QualityAssessmentAgent:
    """Base class for quality assessment agents"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = None
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Assess chapter quality in this agent's dimension"""
        raise NotImplementedError("Subclasses must implement assess method")
    
    def _create_agent(self, name: str, instructions: str, output_type: type):
        """Create an Agents SDK agent with specified configuration"""
        if not env_config.openai_api_key:
            raise RuntimeError("OpenAI API key not configured")
        
        return Agent(
            name=name,
            instructions=instructions,
            model=self.model,
            output_type=output_type
        )


class SemanticAlignmentAgent(QualityAssessmentAgent):
    """Agent specialized in semantic content-syllabus alignment assessment"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)
        self.instructions = """
        You are a Semantic Alignment Specialist responsible for evaluating how well chapter content 
        aligns with syllabus requirements. Your expertise is in:
        
        1. Topic alignment analysis - Does the content match the expected topic?
        2. Learning objectives coverage - Are stated learning objectives addressed?
        3. Key topics verification - Are specified key topics covered appropriately?
        4. Difficulty level assessment - Is complexity appropriate for the target audience?
        5. Semantic coherence - Is the content focused and coherent?
        
        Analyze the provided chapter content against the syllabus section requirements.
        Provide specific, actionable findings with evidence and recommendations.
        Score each dimension on a 0-1 scale where 1 indicates perfect alignment.
        """
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Perform semantic alignment assessment"""
        if not env_config.openai_api_key:
            # Fallback when OpenAI API key is not configured
            return self._fallback_assessment(chapter)
        
        self.agent = self._create_agent(
            name="SemanticAlignmentAgent",
            instructions=self.instructions,
            output_type=AgentAssessment
        )
        
        # Prepare context for assessment
        context = self._prepare_semantic_context(chapter)
        
        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=context
            )
            return result.final_output_as(AgentAssessment)
        except Exception as e:
            logger.error(f"Semantic alignment assessment failed: {e}")
            return self._fallback_assessment(chapter)
    
    def _prepare_semantic_context(self, chapter: ChapterContent) -> str:
        """Prepare context for semantic alignment assessment"""
        context = f"""
        CHAPTER CONTENT ANALYSIS REQUEST
        
        Chapter Details:
        - Section ID: {chapter.section_id}
        - Title: {chapter.title}
        - Content Length: {len(chapter.content)} characters
        
        Content:
        {chapter.content}
        
        """
        
        if chapter.syllabus_section:
            context += f"""
        SYLLABUS REQUIREMENTS:
        - Expected Title: {chapter.syllabus_section.get('title', 'N/A')}
        - Learning Objectives: {chapter.syllabus_section.get('learning_objectives', [])}
        - Key Topics: {chapter.syllabus_section.get('key_topics', [])}
        - Difficulty Level: {chapter.syllabus_section.get('difficulty_level', 'Not specified')}
        - Target Audience: {chapter.syllabus_section.get('target_audience', 'Not specified')}
        """
        else:
            context += "\nSYLLABUS REQUIREMENTS: Not provided - assess content coherence and focus only."
        
        context += """
        
        ASSESSMENT TASK:
        Evaluate semantic alignment between the chapter content and syllabus requirements.
        Provide scores (0-1) for each alignment dimension and specific findings with evidence.
        Focus on identifying semantic mismatches that basic keyword matching would miss.
        """
        
        return context
    
    def _fallback_assessment(self, chapter: ChapterContent) -> AgentAssessment:
        """Fallback assessment when Agents SDK is not available"""
        logger.warning("Using fallback semantic alignment assessment")
        
        findings = []
        score = 0.8  # Default reasonable score
        
        if chapter.syllabus_section:
            # Basic checks that can be done without LLM
            objectives = chapter.syllabus_section.get('learning_objectives', [])
            if objectives and not any(obj.lower() in chapter.content.lower() for obj in objectives):
                findings.append({
                    "description": "Learning objectives not clearly addressed in content",
                    "severity": "WARNING",
                    "confidence": "medium",
                    "category": "content_syllabus_alignment",
                    "evidence": ["No clear reference to stated learning objectives"],
                    "recommendations": ["Add explicit coverage of learning objectives"]
                })
                score -= 0.2
        
        return AgentAssessment(
            dimension="semantic_alignment",
            overall_score=score,
            confidence="medium",
            findings=findings,
            recommendations=["Enable Agents SDK for sophisticated semantic analysis"],
            evidence_summary="Basic pattern matching assessment performed"
        )


class PedagogicalQualityAgent(QualityAssessmentAgent):
    """Agent specialized in pedagogical quality and learning design assessment"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)
        self.instructions = """
        You are a Pedagogical Quality Specialist with expertise in instructional design and learning theory.
        Your role is to evaluate the educational effectiveness of training content across these dimensions:
        
        1. Learning Scaffolding - Progressive building of understanding
        2. Knowledge Anchoring - Connection to prior knowledge and real-world examples
        3. Engagement Elements - Interactive components, questions, activities
        4. Active Learning - Opportunities for learner participation and practice
        5. Instructional Design - Overall structure and learning flow
        
        Evaluate content based on established pedagogical principles and adult learning theory.
        Identify specific pedagogical strengths and weaknesses with actionable recommendations.
        Score each dimension on a 0-1 scale where 1 indicates excellent pedagogical quality.
        """
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Perform pedagogical quality assessment"""
        if not env_config.openai_api_key:
            return self._fallback_pedagogical_assessment(chapter)
        
        self.agent = self._create_agent(
            name="PedagogicalQualityAgent", 
            instructions=self.instructions,
            output_type=AgentAssessment
        )
        
        context = self._prepare_pedagogical_context(chapter)
        
        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=context
            )
            return result.final_output_as(AgentAssessment)
        except Exception as e:
            logger.error(f"Pedagogical quality assessment failed: {e}")
            return self._fallback_pedagogical_assessment(chapter)
    
    def _prepare_pedagogical_context(self, chapter: ChapterContent) -> str:
        """Prepare context for pedagogical assessment"""
        return f"""
        PEDAGOGICAL QUALITY ASSESSMENT REQUEST
        
        Chapter to Evaluate:
        Title: {chapter.title}
        Content: {chapter.content}
        
        ASSESSMENT CRITERIA:
        
        1. Learning Scaffolding:
        - Does content build progressively from simple to complex?
        - Are new concepts introduced systematically?
        - Is prior knowledge appropriately activated?
        
        2. Knowledge Anchoring:
        - Are abstract concepts connected to concrete examples?
        - Is content related to learners' existing knowledge?
        - Are real-world applications provided?
        
        3. Engagement Elements:
        - Are there questions to stimulate thinking?
        - Are interactive elements included?
        - Does content maintain learner interest?
        
        4. Active Learning:
        - Are there opportunities for practice?
        - Can learners apply concepts immediately?
        - Are there reflection prompts?
        
        5. Instructional Design:
        - Is content well-structured with clear sections?
        - Are transitions smooth and logical?
        - Is the learning flow appropriate?
        
        Provide specific findings with evidence from the content and actionable recommendations
        for pedagogical improvement.
        """
    
    def _fallback_pedagogical_assessment(self, chapter: ChapterContent) -> AgentAssessment:
        """Fallback pedagogical assessment"""
        logger.warning("Using fallback pedagogical assessment")
        
        findings = []
        score = 0.7
        
        # Basic pedagogical checks
        content_lower = chapter.content.lower()
        has_questions = '?' in chapter.content
        has_examples = any(word in content_lower for word in ['example', 'for instance', 'such as'])
        has_structure = any(word in content_lower for word in ['introduction', 'summary', 'conclusion'])
        
        if not has_questions:
            findings.append({
                "description": "Content lacks engagement through questions",
                "severity": "WARNING", 
                "confidence": "high",
                "category": "training_principles_violations",
                "evidence": ["No questions found in content"],
                "recommendations": ["Add thought-provoking questions to engage learners"]
            })
            score -= 0.1
            
        if not has_examples:
            findings.append({
                "description": "Limited knowledge anchoring through examples",
                "severity": "INFO",
                "confidence": "medium", 
                "category": "training_principles_violations",
                "evidence": ["Few concrete examples provided"],
                "recommendations": ["Include more real-world examples and analogies"]
            })
            score -= 0.1
        
        return AgentAssessment(
            dimension="pedagogical_quality",
            overall_score=score,
            confidence="medium",
            findings=findings,
            recommendations=["Enable Agents SDK for comprehensive pedagogical analysis"],
            evidence_summary="Basic pedagogical pattern detection performed"
        )


class GroundednessAgent(QualityAssessmentAgent):
    """Agent specialized in content groundedness and evidence quality assessment"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)
        self.instructions = """
        You are a Groundedness Assessment Specialist focused on evaluating the evidential quality
        and factual foundation of educational content. Your expertise includes:
        
        1. Evidence Quality - Are claims supported by appropriate evidence?
        2. Claim Substantiation - Are assertions backed by credible sources or reasoning?
        3. Factual Accuracy - Does content appear factually correct and current?
        4. Source Attribution - Are sources appropriately cited or referenced?
        5. Bias Detection - Are there unsupported generalizations or biased statements?
        
        Identify unsupported claims, overgeneralizations, and statements that lack evidence.
        Flag content that makes absolute statements without qualification.
        Score each dimension on a 0-1 scale where 1 indicates excellent groundedness.
        """
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Perform groundedness assessment"""
        if not env_config.openai_api_key:
            return self._fallback_groundedness_assessment(chapter)
        
        self.agent = self._create_agent(
            name="GroundednessAgent",
            instructions=self.instructions, 
            output_type=AgentAssessment
        )
        
        context = f"""
        GROUNDEDNESS ASSESSMENT REQUEST
        
        Content to Evaluate:
        {chapter.content}
        
        ASSESSMENT FOCUS:
        - Identify claims that lack supporting evidence
        - Flag overgeneralizations and absolute statements
        - Evaluate appropriateness of confidence levels in assertions
        - Check for potential factual inaccuracies
        - Assess need for source attribution
        
        Provide specific examples of groundedness issues with recommendations for improvement.
        """
        
        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=context
            )
            return result.final_output_as(AgentAssessment)
        except Exception as e:
            logger.error(f"Groundedness assessment failed: {e}")
            return self._fallback_groundedness_assessment(chapter)
    
    def _fallback_groundedness_assessment(self, chapter: ChapterContent) -> AgentAssessment:
        """Fallback groundedness assessment"""
        logger.warning("Using fallback groundedness assessment")
        
        findings = []
        score = 0.8
        
        # Basic groundedness checks
        content_lower = chapter.content.lower()
        problematic_phrases = [
            "everyone knows", "obviously", "clearly", "without a doubt",
            "it goes without saying", "universally", "always", "never"
        ]
        
        for phrase in problematic_phrases:
            if phrase in content_lower:
                findings.append({
                    "description": f"Potentially unsupported claim: '{phrase}'",
                    "severity": "WARNING",
                    "confidence": "high",
                    "category": "groundedness_violations", 
                    "evidence": [f"Found phrase '{phrase}' indicating absolute claim"],
                    "recommendations": ["Qualify statements and provide supporting evidence"]
                })
                score -= 0.1
        
        return AgentAssessment(
            dimension="groundedness",
            overall_score=max(0.0, score),
            confidence="medium",
            findings=findings,
            recommendations=["Enable Agents SDK for sophisticated groundedness analysis"],
            evidence_summary="Basic pattern matching for unsupported claims performed"
        )


class ContentDepthAgent(QualityAssessmentAgent):
    """Agent specialized in content depth and complexity assessment"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)
        self.instructions = """
        You are a Content Depth Specialist responsible for evaluating whether content complexity
        and depth are appropriate for the intended audience and learning objectives. Assess:
        
        1. Complexity Appropriateness - Is difficulty level suitable for target audience?
        2. Conceptual Depth - Is coverage sufficiently deep for learning objectives?
        3. Technical Rigor - Is technical content accurate and appropriately detailed?
        4. Audience Alignment - Does content match audience knowledge level and needs?
        5. Progressive Complexity - Does content build complexity appropriately?
        
        Consider factors like prerequisite knowledge, learning objectives, and target audience.
        Identify content that is too shallow, too complex, or inappropriately paced.
        Score each dimension on a 0-1 scale where 1 indicates optimal depth.
        """
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Perform content depth assessment"""
        if not env_config.openai_api_key:
            return self._fallback_depth_assessment(chapter)
        
        self.agent = self._create_agent(
            name="ContentDepthAgent",
            instructions=self.instructions,
            output_type=AgentAssessment
        )
        
        context = self._prepare_depth_context(chapter)
        
        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=context
            )
            return result.final_output_as(AgentAssessment)
        except Exception as e:
            logger.error(f"Content depth assessment failed: {e}")
            return self._fallback_depth_assessment(chapter)
    
    def _prepare_depth_context(self, chapter: ChapterContent) -> str:
        """Prepare context for depth assessment"""
        context = f"""
        CONTENT DEPTH ASSESSMENT REQUEST
        
        Content: {chapter.content}
        
        """
        
        if chapter.syllabus_section:
            context += f"""
        TARGET SPECIFICATIONS:
        - Difficulty Level: {chapter.syllabus_section.get('difficulty_level', 'Not specified')}
        - Target Audience: {chapter.syllabus_section.get('target_audience', 'Not specified')}
        - Prerequisites: {chapter.syllabus_section.get('prerequisite_knowledge', 'Not specified')}
        - Learning Objectives: {chapter.syllabus_section.get('learning_objectives', [])}
        """
        
        context += """
        
        ASSESSMENT CRITERIA:
        - Is content depth appropriate for specified difficulty level?
        - Does technical detail match audience expertise?
        - Are learning objectives achievable with this depth?
        - Is complexity progression logical and manageable?
        
        Identify specific depth issues and provide recommendations for optimization.
        """
        
        return context
    
    def _fallback_depth_assessment(self, chapter: ChapterContent) -> AgentAssessment:
        """Fallback depth assessment"""
        logger.warning("Using fallback content depth assessment")
        
        findings = []
        score = 0.75
        
        # Basic depth analysis
        word_count = len(chapter.content.split())
        
        if word_count < 100:
            findings.append({
                "description": f"Content appears too shallow ({word_count} words)",
                "severity": "WARNING",
                "confidence": "medium",
                "category": "inadequate_level",
                "evidence": [f"Word count: {word_count}"],
                "recommendations": ["Expand content with more detailed explanations and examples"]
            })
            score -= 0.2
        
        return AgentAssessment(
            dimension="content_depth",
            overall_score=score,
            confidence="low",
            findings=findings,
            recommendations=["Enable Agents SDK for comprehensive depth analysis"],
            evidence_summary="Basic word count and structure analysis performed"
        )


class GuidelinesComplianceAgent(QualityAssessmentAgent):
    """Agent specialized in training course guidelines compliance assessment"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(model)
        self.instructions = """
        You are a Training Guidelines Compliance Specialist responsible for ensuring content
        adheres to established training course principles and standards. Evaluate:
        
        1. Structure Compliance - Does content follow recommended structural patterns?
        2. Tone Appropriateness - Is writing style suitable for training context?
        3. Pacing Quality - Is information presented at appropriate pace?
        4. Accessibility - Is content accessible to diverse learners?
        5. Professional Standards - Does content meet professional training standards?
        
        Check for compliance with training course guidelines including:
        - Clear section organization
        - Appropriate professional tone
        - Manageable information chunks
        - Inclusive language
        - Consistent formatting
        
        Score each dimension on a 0-1 scale where 1 indicates full compliance.
        """
        
    async def assess(self, chapter: ChapterContent) -> AgentAssessment:
        """Perform guidelines compliance assessment"""
        if not env_config.openai_api_key:
            return self._fallback_compliance_assessment(chapter)
        
        self.agent = self._create_agent(
            name="GuidelinesComplianceAgent",
            instructions=self.instructions,
            output_type=AgentAssessment
        )
        
        # Load training guidelines if available
        guidelines_content = self._load_training_guidelines()
        
        context = f"""
        GUIDELINES COMPLIANCE ASSESSMENT REQUEST
        
        Content to Evaluate: {chapter.content}
        
        Training Guidelines: {guidelines_content}
        
        COMPLIANCE CHECKLIST:
        - Structural organization and flow
        - Professional tone and language
        - Information pacing and chunking
        - Accessibility and inclusivity
        - Formatting consistency
        
        Identify specific compliance issues and provide remediation recommendations.
        """
        
        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=context
            )
            return result.final_output_as(AgentAssessment)
        except Exception as e:
            logger.error(f"Guidelines compliance assessment failed: {e}")
            return self._fallback_compliance_assessment(chapter)
    
    def _load_training_guidelines(self) -> str:
        """Load training course guidelines"""
        try:
            guidelines_path = Path(__file__).parent.parent / "guidelines" / "training_course_guidelines.md"
            with open(guidelines_path, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Training guidelines not found - using default compliance standards"
    
    def _fallback_compliance_assessment(self, chapter: ChapterContent) -> AgentAssessment:
        """Fallback compliance assessment"""
        logger.warning("Using fallback guidelines compliance assessment")
        
        findings = []
        score = 0.8
        
        # Basic compliance checks
        content = chapter.content
        
        # Check for basic structure
        has_clear_sections = any(marker in content for marker in ['##', '**', 'Introduction', 'Summary'])
        if not has_clear_sections:
            findings.append({
                "description": "Content lacks clear structural organization",
                "severity": "INFO",
                "confidence": "medium",
                "category": "training_principles_violations",
                "evidence": ["No clear section markers found"],
                "recommendations": ["Add clear section headings and organization"]
            })
            score -= 0.1
        
        return AgentAssessment(
            dimension="guidelines_compliance",
            overall_score=score,
            confidence="medium",
            findings=findings,
            recommendations=["Enable Agents SDK for comprehensive compliance analysis"],
            evidence_summary="Basic structural and formatting analysis performed"
        )


class QualityConsensusOrchestrator:
    """Orchestrates multiple quality assessment agents and builds consensus"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agents = {
            QualityDimension.SEMANTIC_ALIGNMENT: SemanticAlignmentAgent(model),
            QualityDimension.PEDAGOGICAL_QUALITY: PedagogicalQualityAgent(model),
            QualityDimension.GROUNDEDNESS: GroundednessAgent(model),
            QualityDimension.CONTENT_DEPTH: ContentDepthAgent(model),
            QualityDimension.GUIDELINES_COMPLIANCE: GuidelinesComplianceAgent(model)
        }
        
    async def assess_chapter(self, chapter: ChapterContent) -> dict[str, Any]:
        """Coordinate multi-agent assessment of chapter quality"""
        logger.info(f"Starting multi-agent quality assessment for chapter: {chapter.section_id}")
        
        # Run all agents in parallel
        assessment_tasks = []
        for dimension, agent in self.agents.items():
            task = asyncio.create_task(agent.assess(chapter))
            assessment_tasks.append((dimension, task))
        
        # Collect results
        agent_assessments = {}
        for dimension, task in assessment_tasks:
            try:
                assessment = await task
                agent_assessments[dimension.value] = assessment
                logger.info(f"Completed {dimension.value} assessment: score={assessment.overall_score}")
            except Exception as e:
                logger.error(f"Assessment failed for {dimension.value}: {e}")
                # Use fallback assessment
                agent_assessments[dimension.value] = self._create_fallback_assessment(dimension.value)
        
        # Build consensus assessment
        consensus = self._build_consensus(agent_assessments)
        
        logger.info(f"Multi-agent assessment completed for {chapter.section_id}: overall_score={consensus['overall_quality_score']}")
        return consensus
    
    def _build_consensus(self, agent_assessments: dict[str, AgentAssessment]) -> dict[str, Any]:
        """Build consensus from individual agent assessments"""
        
        # Calculate weighted overall score
        dimension_weights = {
            "semantic_alignment": 0.25,
            "pedagogical_quality": 0.25,
            "groundedness": 0.20,
            "content_depth": 0.15,
            "guidelines_compliance": 0.15
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for dimension, assessment in agent_assessments.items():
            weight = dimension_weights.get(dimension, 0.1)
            weighted_score += assessment.overall_score * weight
            total_weight += weight
        
        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Collect all findings
        all_findings = []
        all_recommendations = []
        
        for dimension, assessment in agent_assessments.items():
            all_findings.extend(assessment.findings)
            all_recommendations.extend(assessment.recommendations)
        
        # Calculate confidence based on agent agreement
        scores = [assessment.overall_score for assessment in agent_assessments.values()]
        score_variance = sum((score - overall_score) ** 2 for score in scores) / len(scores)
        consensus_confidence = max(0.0, 1.0 - score_variance * 2)  # Higher variance = lower confidence
        
        # Convert agent assessments to dictionaries safely
        agent_assessments_dict = {}
        for dim, assessment in agent_assessments.items():
            if hasattr(assessment, '__dict__'):
                # For AgentAssessment objects, convert to dict manually
                agent_assessments_dict[dim] = {
                    "dimension": assessment.dimension,
                    "overall_score": assessment.overall_score,
                    "confidence": assessment.confidence,
                    "findings": assessment.findings,
                    "recommendations": assessment.recommendations,
                    "evidence_summary": assessment.evidence_summary
                }
            else:
                # Fallback for dictionaries or other types
                agent_assessments_dict[dim] = assessment
        
        return {
            "overall_quality_score": round(overall_score, 3),
            "consensus_confidence": round(consensus_confidence, 3),
            "agent_assessments": agent_assessments_dict,
            "consolidated_findings": all_findings,
            "consolidated_recommendations": list(set(all_recommendations)),
            "dimension_scores": {dim: assessment.overall_score for dim, assessment in agent_assessments.items()},
            "assessment_metadata": {
                "agents_used": list(agent_assessments.keys()),
                "assessment_timestamp": asyncio.get_event_loop().time(),
                "model_used": self.model
            }
        }
    
    def _create_fallback_assessment(self, dimension: str) -> AgentAssessment:
        """Create fallback assessment when agent fails"""
        return AgentAssessment(
            dimension=dimension,
            overall_score=0.5,  # Neutral score
            confidence="low",
            findings=[{
                "description": f"Agent assessment failed for {dimension}",
                "severity": "WARNING",
                "confidence": "low",
                "category": "assessment_failure",
                "evidence": ["Agent execution error"],
                "recommendations": ["Review agent configuration and retry assessment"]
            }],
            recommendations=[f"Retry {dimension} assessment"],
            evidence_summary="Fallback assessment due to agent failure"
        )