import pytest
from app.services.validation_service import validation_service

def test_evidence_validation_exact_match(sample_transcript_segments):
    decision_item = {
        "description": "Selected PostgreSQL as transactional database",
        "timestamp": 15.0,
        "evidence": "We finalized the choice of PostgreSQL as our primary transactional database.",
        "confidence": 0.9,
        "validation_status": "unverified"
    }

    validated = validation_service.validate_item(decision_item, sample_transcript_segments)
    assert validated["validation_status"] == "verified"
    assert validated["confidence"] >= 0.9

def test_evidence_validation_partial_match(sample_transcript_segments):
    action_item = {
        "task": "Prepare the data migration script",
        "owner": "Sarah",
        "deadline": "Friday",
        "timestamp": 29.0,
        "evidence": "Sarah will prepare data migration script",
        "confidence": 0.85,
        "validation_status": "unverified"
    }

    validated = validation_service.validate_item(action_item, sample_transcript_segments)
    assert validated["validation_status"] == "verified"
    assert validated["timestamp"] == 29.0

def test_evidence_validation_flagged_for_fabricated_evidence(sample_transcript_segments):
    fabricated_item = {
        "description": "We decided to rebuild the entire frontend in Rust WebAssembly",
        "timestamp": 0.0,
        "evidence": "Completely fabricated quote never spoken in the meeting transcript",
        "confidence": 0.8,
        "validation_status": "unverified"
    }

    validated = validation_service.validate_item(fabricated_item, sample_transcript_segments)
    assert validated["validation_status"] == "flagged"
    assert validated["confidence"] <= 0.4

def test_evidence_validation_flagged_for_empty_evidence(sample_transcript_segments):
    empty_evidence_item = {
        "description": "Random unverified claim",
        "timestamp": None,
        "evidence": "",
        "confidence": 0.7,
        "validation_status": "unverified"
    }

    validated = validation_service.validate_item(empty_evidence_item, sample_transcript_segments)
    assert validated["validation_status"] == "flagged"
