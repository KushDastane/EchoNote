import logging
from typing import List, Dict, Any, Tuple

from app.utils.timestamps import format_timestamp
from app.services.llm_service import get_llm_provider, MockLLMProvider
from app.services.validation_service import validation_service
from app.schemas.meeting import LLMExtractionResult

logger = logging.getLogger("echonote.extraction")

class ExtractionService:
    def format_transcript_for_llm(self, segments: List[Dict[str, Any]]) -> str:
        """
        Formats segments into readable [MM:SS] Speaker: text format.
        """
        lines = []
        for s in segments:
            ts = format_timestamp(s.get("start_time", 0.0))
            spk = s.get("speaker", "Speaker")
            txt = s.get("text", "")
            lines.append(f"[{ts}] {spk}: {txt}")
        return "\n".join(lines)

    def extract_and_validate(
        self,
        segments: List[Dict[str, Any]]
    ) -> Tuple[LLMExtractionResult, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs LLM extraction and executes evidence validation.
        Returns:
            (extraction_result, validated_decisions, validated_action_items)
        """
        if not segments:
            empty_result = LLMExtractionResult()
            return empty_result, [], []

        formatted_text = self.format_transcript_for_llm(segments)
        
        provider = get_llm_provider()
        is_mock = isinstance(provider, MockLLMProvider)
        logger.info(f"Using LLM provider: {provider.__class__.__name__} (is_mock={is_mock})")
        
        # Call LLM provider with transcript
        extraction: LLMExtractionResult = provider.extract_meeting_intelligence(formatted_text)

        # Convert extraction items to dicts for validation
        raw_decisions = [d.model_dump() for d in extraction.decisions]
        raw_actions = [a.model_dump() for a in extraction.action_items]

        # Enforce rules: never invent owners or deadlines
        for a in raw_actions:
            if not a.get("owner") or str(a.get("owner")).strip().lower() in ["none", "null", "unknown", ""]:
                a["owner"] = "Not specified"
            if not a.get("deadline") or str(a.get("deadline")).strip().lower() in ["none", "null", "unknown", ""]:
                a["deadline"] = "Not specified"

        # Validate against transcript evidence
        # Pass is_mock=True so mock-generated items are never falsely marked 'verified'
        val_decisions, val_actions = validation_service.validate_all(
            decisions=raw_decisions,
            action_items=raw_actions,
            segments=segments,
            is_mock_provider=is_mock
        )

        return extraction, val_decisions, val_actions

extraction_service = ExtractionService()
