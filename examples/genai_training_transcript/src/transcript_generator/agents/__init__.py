"""
Multi-Agent Quality Assessment System

This module provides sophisticated quality assessment capabilities for the EditorialFinalizer
using OpenAI Agents SDK. It implements specialized agents for different quality dimensions:

- SemanticAlignmentAgent: Content-syllabus semantic alignment
- PedagogicalQualityAgent: Educational effectiveness assessment  
- GroundednessAgent: Evidence quality and factual grounding
- ContentDepthAgent: Content complexity and depth analysis
- GuidelinesComplianceAgent: Training course guidelines adherence
- QualityConsensusOrchestrator: Multi-agent coordination and consensus

This replaces the basic pattern matching approach with sophisticated LLM-based analysis
to properly fulfill US-005 requirements for editorial quality control.
"""

from .quality_assessment_agents import (
    AgentAssessment,
    AssessmentConfidence,
    # Core data structures
    ChapterContent,
    ContentDepthAgent,
    ContentDepthAssessment,
    GroundednessAgent,
    GroundednessAssessment,
    GuidelinesComplianceAgent,
    GuidelinesComplianceAssessment,
    PedagogicalAssessment,
    PedagogicalQualityAgent,
    # Agent implementations
    QualityAssessmentAgent,
    # Orchestration
    QualityConsensusOrchestrator,
    QualityDimension,
    QualityFinding,
    SemanticAlignmentAgent,
    # Specialized assessment models
    SemanticAlignmentAssessment,
)

__all__ = [
    # Data structures
    "ChapterContent",
    "QualityFinding", 
    "AgentAssessment",
    "AssessmentConfidence",
    "QualityDimension",
    
    # Assessment models
    "SemanticAlignmentAssessment",
    "PedagogicalAssessment",
    "GroundednessAssessment", 
    "ContentDepthAssessment",
    "GuidelinesComplianceAssessment",
    
    # Agents
    "QualityAssessmentAgent",
    "SemanticAlignmentAgent",
    "PedagogicalQualityAgent",
    "GroundednessAgent",
    "ContentDepthAgent",
    "GuidelinesComplianceAgent",
    
    # Orchestration
    "QualityConsensusOrchestrator",
]