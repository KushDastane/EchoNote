import pytest
from app.schemas.meeting import (
    LLMExtractionResult,
    LLMDecisionItem,
    LLMActionItem
)
from app.services.llm_service import MockLLMProvider
from app.services.extraction_service import extraction_service

def test_action_item_schema_defaults_not_specified():
    action = LLMActionItem(
        task="Configure cloud backup retention",
        evidence="We will configure cloud backup retention"
    )
    assert action.owner == "Not specified"
    assert action.deadline == "Not specified"
    assert action.status == "pending"

def test_llm_extraction_result_pydantic_validation():
    data = {
        "summary": "Engineering team discussed database strategy and task delegation.",
        "key_points": ["Selected PostgreSQL", "Scheduled migration script"],
        "decisions": [
            {
                "description": "Selected PostgreSQL",
                "speaker": "Speaker 2",
                "timestamp": 15.0,
                "evidence": "We finalized the choice of PostgreSQL",
                "confidence": 0.95
            }
        ],
        "action_items": [
            {
                "task": "Prepare migration script",
                "owner": "Sarah",
                "deadline": "Friday",
                "timestamp": 29.0,
                "evidence": "Sarah will prepare the data migration script by Friday.",
                "status": "pending",
                "confidence": 0.9
            }
        ],
        "unresolved_questions": ["Archive audit logs or migrate to S3?"],
        "important_topics": ["Database", "Migration"]
    }

    result = LLMExtractionResult(**data)
    assert result.summary.startswith("Engineering")
    assert len(result.decisions) == 1
    assert result.decisions[0].confidence == 0.95
    assert len(result.action_items) == 1
    assert result.action_items[0].owner == "Sarah"

def test_extraction_service_enforces_not_specified(sample_transcript_segments):
    # Test end-to-end extraction and validation service pipeline
    result, val_decisions, val_actions = extraction_service.extract_and_validate(sample_transcript_segments)

    assert result.summary
    assert len(val_decisions) >= 1
    assert len(val_actions) >= 1

    for a in val_actions:
        assert a["owner"] is not None
        assert a["deadline"] is not None
        assert a["validation_status"] in ["verified", "unverified", "flagged"]

    for d in val_decisions:
        assert d["validation_status"] in ["verified", "unverified", "flagged"]
