import difflib
from typing import List, Dict, Any, Tuple, Optional

class EvidenceValidationService:
    """
    Evidence-backed verification engine for EchoNote.
    Ensures that every decision and action item references real transcript data.

    Key distinction:
    - 'verified'   → Evidence string found (substring or high similarity) in a real transcript segment.
    - 'unverified' → Partial match found but not conclusive.
    - 'flagged'    → No evidence provided, or no match found in transcript.

    When the LLM provider is mock, ALL items are marked 'unverified' at best — never 'verified' —
    because heuristic keyword extraction cannot guarantee the claims are factually grounded.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for evidence comparison."""
        if not text:
            return ""
        import re
        return re.sub(r"[^\w\s]", "", text.lower()).strip()

    def find_best_transcript_match(
        self,
        evidence: Optional[str],
        segments: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Searches transcript segments for the excerpt cited as evidence.
        Returns the best matching segment and a match ratio between 0.0 and 1.0.
        """
        if not evidence or not segments:
            return None, 0.0

        norm_evidence = self._normalize(evidence)
        if not norm_evidence:
            return None, 0.0

        best_segment = None
        best_ratio = 0.0

        for seg in segments:
            seg_text = seg.get("text", "")
            norm_seg = self._normalize(seg_text)

            # Direct substring match
            if norm_evidence in norm_seg or norm_seg in norm_evidence:
                return seg, 1.0

            # Sequence matcher ratio
            ratio = difflib.SequenceMatcher(None, norm_evidence, norm_seg).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_segment = seg

        return best_segment, best_ratio

    def validate_item(
        self,
        item: Dict[str, Any],
        segments: List[Dict[str, Any]],
        is_mock_provider: bool = False
    ) -> Dict[str, Any]:
        """
        Validates a single decision or action item against the transcript.
        Assigns 'verified', 'unverified', or 'flagged'.

        Args:
            item: The decision or action item dict.
            segments: Transcript segments to match against.
            is_mock_provider: When True, never mark as 'verified' — mock output
                              is heuristic only and cannot be considered ground truth.
        """
        validated = dict(item)
        evidence = validated.get("evidence", "")

        if not evidence or not evidence.strip():
            validated["validation_status"] = "flagged"
            validated["confidence"] = min(validated.get("confidence", 0.5), 0.3)
            return validated

        best_match, ratio = self.find_best_transcript_match(evidence, segments)

        if best_match and ratio >= 0.65 and not is_mock_provider:
            # Only mark 'verified' for real LLM providers with real transcript evidence
            validated["validation_status"] = "verified"
            if validated.get("timestamp") is None or validated.get("timestamp") <= 0:
                validated["timestamp"] = best_match.get("start_time", 0.0)
            validated["confidence"] = max(validated.get("confidence", 0.8), 0.9)
        elif best_match and ratio >= 0.65 and is_mock_provider:
            # Mock provider: high text similarity but heuristic — mark unverified
            validated["validation_status"] = "unverified"
            validated["confidence"] = min(validated.get("confidence", 0.7), 0.7)
            if validated.get("timestamp") is None:
                validated["timestamp"] = best_match.get("start_time", 0.0)
        elif best_match and ratio >= 0.40:
            validated["validation_status"] = "unverified"
            if validated.get("timestamp") is None:
                validated["timestamp"] = best_match.get("start_time", 0.0)
        else:
            validated["validation_status"] = "flagged"
            validated["confidence"] = min(validated.get("confidence", 0.5), 0.4)

        return validated

    def validate_all(
        self,
        decisions: List[Dict[str, Any]],
        action_items: List[Dict[str, Any]],
        segments: List[Dict[str, Any]],
        is_mock_provider: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validates all decisions and action items.

        Args:
            decisions: Extracted decision dicts.
            action_items: Extracted action item dicts.
            segments: Transcript segments to validate against.
            is_mock_provider: Pass True when extraction came from MockLLMProvider
                              so items can never be falsely marked 'verified'.
        """
        validated_decisions = [self.validate_item(d, segments, is_mock_provider) for d in decisions]
        validated_actions = [self.validate_item(a, segments, is_mock_provider) for a in action_items]
        return validated_decisions, validated_actions

validation_service = EvidenceValidationService()
