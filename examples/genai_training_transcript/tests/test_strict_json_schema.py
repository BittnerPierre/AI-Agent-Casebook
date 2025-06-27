"""
Test for Strict JSON Schema Compatibility

This test validates that our Pydantic models are compatible with 
OpenAI's strict JSON schema requirements.
"""

import pytest
from pydantic import ValidationError

from transcript_generator.agents.quality_assessment_agents import (
    AgentAssessment,
    ConfidenceLevel,
    FindingSeverity,
    QualityFindingStrict
)


class TestStrictJSONSchemaCompatibility:
    """Test that models are strict JSON schema compatible"""
    
    def test_finding_severity_enum(self):
        """Test that FindingSeverity enum works correctly"""
        assert FindingSeverity.INFO.value == "INFO"
        assert FindingSeverity.WARNING.value == "WARNING"
        assert FindingSeverity.ERROR.value == "ERROR"
    
    def test_confidence_level_enum(self):
        """Test that ConfidenceLevel enum works correctly"""
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.VERY_HIGH.value == "very_high"
    
    def test_quality_finding_strict_creation(self):
        """Test that QualityFindingStrict can be created with valid data"""
        finding = QualityFindingStrict(
            description="Test finding",
            severity=FindingSeverity.WARNING,
            confidence=ConfidenceLevel.HIGH,
            category="test_category",
            evidence=["Evidence 1", "Evidence 2"],
            recommendations=["Fix this", "Improve that"]
        )
        
        assert finding.description == "Test finding"
        assert finding.severity == FindingSeverity.WARNING
        assert finding.confidence == ConfidenceLevel.HIGH
        assert finding.category == "test_category"
        assert finding.evidence == ["Evidence 1", "Evidence 2"]
        assert finding.recommendations == ["Fix this", "Improve that"]
    
    def test_quality_finding_strict_validation(self):
        """Test that QualityFindingStrict validates required fields"""
        with pytest.raises(ValidationError):
            QualityFindingStrict()  # Missing required fields
    
    def test_agent_assessment_creation(self):
        """Test that AgentAssessment can be created with strict findings"""
        finding = QualityFindingStrict(
            description="Test finding",
            severity=FindingSeverity.INFO,
            confidence=ConfidenceLevel.MEDIUM,
            category="test",
            evidence=["test evidence"],
            recommendations=["test recommendation"]
        )
        
        assessment = AgentAssessment(
            dimension="test_dimension",
            overall_score=0.8,
            confidence=ConfidenceLevel.HIGH,
            findings=[finding],
            recommendations=["Overall recommendation"],
            evidence_summary="Test evidence summary"
        )
        
        assert assessment.dimension == "test_dimension"
        assert assessment.overall_score == 0.8
        assert assessment.confidence == ConfidenceLevel.HIGH
        assert len(assessment.findings) == 1
        assert assessment.findings[0].description == "Test finding"
    
    def test_agent_assessment_score_validation(self):
        """Test that AgentAssessment validates score range"""
        finding = QualityFindingStrict(
            description="Test",
            severity=FindingSeverity.INFO,
            confidence=ConfidenceLevel.LOW,
            category="test",
            evidence=["test"],
            recommendations=["test"]
        )
        
        # Valid score
        assessment = AgentAssessment(
            dimension="test",
            overall_score=0.5,
            confidence=ConfidenceLevel.MEDIUM,
            findings=[finding],
            recommendations=["test"],
            evidence_summary="test"
        )
        assert assessment.overall_score == 0.5
        
        # Invalid score (too high)
        with pytest.raises(ValidationError):
            AgentAssessment(
                dimension="test",
                overall_score=1.5,  # Invalid: > 1
                confidence=ConfidenceLevel.MEDIUM,
                findings=[finding],
                recommendations=["test"],
                evidence_summary="test"
            )
        
        # Invalid score (too low)
        with pytest.raises(ValidationError):
            AgentAssessment(
                dimension="test",
                overall_score=-0.1,  # Invalid: < 0
                confidence=ConfidenceLevel.MEDIUM,
                findings=[finding],
                recommendations=["test"],
                evidence_summary="test"
            )
    
    def test_json_serialization_compatibility(self):
        """Test that models can be serialized to JSON (for dict conversion)"""
        finding = QualityFindingStrict(
            description="Test finding",
            severity=FindingSeverity.ERROR,
            confidence=ConfidenceLevel.VERY_HIGH,
            category="test_category",
            evidence=["Strong evidence"],
            recommendations=["Critical fix needed"]
        )
        
        # Test that model can be converted to dict
        finding_dict = finding.model_dump()
        
        assert finding_dict["description"] == "Test finding"
        assert finding_dict["severity"] == FindingSeverity.ERROR
        assert finding_dict["confidence"] == ConfidenceLevel.VERY_HIGH
        assert finding_dict["category"] == "test_category"
        assert finding_dict["evidence"] == ["Strong evidence"]
        assert finding_dict["recommendations"] == ["Critical fix needed"]
    
    def test_enum_value_extraction(self):
        """Test extracting string values from enums for JSON serialization"""
        finding = QualityFindingStrict(
            description="Test",
            severity=FindingSeverity.WARNING,
            confidence=ConfidenceLevel.HIGH,
            category="test",
            evidence=["test"],
            recommendations=["test"]
        )
        
        # Test that we can extract string values for JSON serialization
        severity_str = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity)
        confidence_str = finding.confidence.value if hasattr(finding.confidence, 'value') else str(finding.confidence)
        
        assert severity_str == "WARNING"
        assert confidence_str == "high" 