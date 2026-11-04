import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.config import settings
from app.schemas.meeting import LLMExtractionResult, LLMDecisionItem, LLMActionItem

logger = logging.getLogger("echonote.llm")

SYSTEM_EXTRACTION_PROMPT = """You are an expert AI meeting analyst for EchoNote, an evidence-backed meeting intelligence platform.
Your task is to analyze the following meeting transcript segments and extract structured meeting intelligence.

RULES YOU MUST FOLLOW STRICTLY:
1. Every extracted Decision or Action Item MUST cite the exact transcript text as 'evidence' and provide the corresponding timestamp in seconds.
2. NEVER invent or infer an owner for an action item. If no specific person or role is committed to doing it, set 'owner' explicitly to "Not specified".
3. NEVER invent or assume deadlines. If no specific date or timeframe was mentioned, set 'deadline' explicitly to "Not specified".
4. Distinguish casual discussions or suggestions from actual agreed decisions. Only record genuine consensus/agreements as decisions.
5. If an item has insufficient evidence in the transcript, DO NOT invent it.
6. Return ONLY valid JSON adhering strictly to the following schema without any markdown wrap or preamble.

SCHEMA:
{
  "summary": "Concise 2-3 paragraph executive summary of what was discussed and concluded.",
  "key_points": [
    "Important discussion point 1",
    "Important discussion point 2"
  ],
  "decisions": [
    {
      "description": "Concrete decision made",
      "speaker": "Speaker name or Speaker placeholder",
      "timestamp": 12.5,
      "evidence": "Direct quote from transcript verifying this decision",
      "confidence": 0.95
    }
  ],
  "action_items": [
    {
      "task": "Specific actionable task",
      "owner": "Name of assigned owner, or 'Not specified'",
      "deadline": "Stated deadline, or 'Not specified'",
      "timestamp": 45.0,
      "evidence": "Direct quote from transcript verifying this assignment",
      "status": "pending",
      "confidence": 0.9
    }
  ],
  "unresolved_questions": [
    "Open question or blocker left unanswered in meeting"
  ],
  "important_topics": [
    "Core topic or theme"
  ]
}
"""

class BaseLLMProvider(ABC):
    @abstractmethod
    def extract_meeting_intelligence(self, formatted_transcript: str) -> LLMExtractionResult:
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Heuristic-only provider for offline development and automated tests.

    IMPORTANT: This provider operates WITHOUT a real language model.
    It uses keyword matching only. It will NEVER fabricate decisions or action
    items — if none are found in the actual transcript text, it returns empty lists.
    Use a real LLM provider (openai / gemini) for production-quality extraction.
    """
    def extract_meeting_intelligence(self, formatted_transcript: str) -> LLMExtractionResult:
        logger.warning(
            "MockLLMProvider is active. Extraction uses keyword heuristics only — "
            "no real LLM is running. Set LLM_PROVIDER=openai or LLM_PROVIDER=gemini "
            "with a valid LLM_API_KEY in backend/.env for real AI extraction."
        )
        lines = [line.strip() for line in formatted_transcript.splitlines() if line.strip()]
        
        decisions: List[LLMDecisionItem] = []
        action_items: List[LLMActionItem] = []
        key_points: List[str] = []
        unresolved: List[str] = []
        topics: List[str] = []

        decision_triggers = ["decided", "agreed", "approved", "confirmed", "settled on", "finalized", "chosen"]
        action_triggers = ["will", "take care of", "action item", "follow up", "handle", "responsible for", "prepare", "send", "review"]
        question_triggers = ["?", "unclear", "wondering", "not sure", "follow-up on", "open question"]

        for line in lines:
            # Parse [MM:SS] Speaker: text
            timestamp = 0.0
            speaker = "Speaker 1"
            content = line

            if line.startswith("[") and "]" in line:
                ts_part = line[1:line.find("]")]
                parts = ts_part.split(":")
                try:
                    if len(parts) == 2:
                        timestamp = float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3:
                        timestamp = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    timestamp = 0.0
                
                rest = line[line.find("]") + 1:].strip()
                if ":" in rest:
                    spk, text = rest.split(":", 1)
                    speaker = spk.strip()
                    content = text.strip()
                else:
                    content = rest

            lower = content.lower()

            # Check for decisions
            if any(trig in lower for trig in decision_triggers):
                decisions.append(LLMDecisionItem(
                    description=content.capitalize(),
                    speaker=speaker,
                    timestamp=timestamp,
                    evidence=content,
                    confidence=0.92
                ))

            # Check for action items
            if any(trig in lower for trig in action_triggers):
                # Check for explicit owner
                owner = "Not specified"
                words = content.split()
                # Check for "I will", "John will", "Sarah will"
                for i, w in enumerate(words):
                    if w.lower() == "will" and i > 0:
                        candidate = words[i - 1].strip(",.")
                        if candidate.lower() not in ["we", "this", "it", "that", "there"]:
                            owner = candidate
                        elif candidate.lower() == "we":
                            owner = "Team"
                        elif candidate.lower() in ["i", "me"]:
                            owner = speaker

                # Check for deadline
                deadline = "Not specified"
                deadline_indicators = ["by friday", "by monday", "tomorrow", "next week", "end of day", "by eod", "by tuesday", "by wednesday", "by thursday"]
                for dl in deadline_indicators:
                    if dl in lower:
                        deadline = dl.title()
                        break

                action_items.append(LLMActionItem(
                    task=content.capitalize(),
                    owner=owner,
                    deadline=deadline,
                    timestamp=timestamp,
                    evidence=content,
                    status="pending",
                    confidence=0.88
                ))

            # Check for unresolved questions
            if any(trig in lower for trig in question_triggers):
                unresolved.append(content)

            # Collect key discussion points
            if len(content) > 30 and len(key_points) < 6:
                key_points.append(content)

        # Default synthesis summary based on actual line count
        summary_text = (
            f"The meeting covered {len(lines)} discussion turns."
            if lines else "No transcript content was available to summarize."
        )

        # NOTE: If no decisions or action items were found via keyword matching,
        # return empty lists. Do NOT fabricate placeholder entries.

        topics = list(dict.fromkeys(
            [t for t in ["Architecture", "Planning", "Roadmap", "Deliverables"] if any(t.lower() in l.lower() for l in lines)]
        ))[:4]

        return LLMExtractionResult(
            summary=summary_text,
            key_points=key_points[:5],
            decisions=decisions,
            action_items=action_items,
            unresolved_questions=unresolved[:4],
            important_topics=topics
        )


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def extract_meeting_intelligence(self, formatted_transcript: str) -> LLMExtractionResult:
        if not self.client or not self.api_key:
            raise RuntimeError(
                "OpenAI provider selected but client or API key is not configured. "
                "Set LLM_API_KEY in backend/.env. Will not fall back to mock silently."
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Analyze the following meeting transcript:\n\n{formatted_transcript}"}
                ],
                temperature=0.1
            )
            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            return LLMExtractionResult(**data)
        except Exception as e:
            logger.error(f"OpenAI extraction call failed: {e}")
            raise RuntimeError(f"OpenAI API call failed: {e}")


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model
        import requests
        self._requests = requests

    def extract_meeting_intelligence(self, formatted_transcript: str) -> LLMExtractionResult:
        if not self.api_key:
            raise RuntimeError(
                "Gemini provider selected but LLM_API_KEY is not configured. "
                "Set LLM_API_KEY in backend/.env. Will not fall back to mock silently."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_EXTRACTION_PROMPT}\n\nMeeting Transcript:\n{formatted_transcript}"}
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        try:
            res = self._requests.post(url, json=payload, timeout=45)
            res.raise_for_status()
            res_data = res.json()
            text_resp = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text_resp)
            return LLMExtractionResult(**parsed)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise RuntimeError(f"Gemini API call failed: {e}")


def get_llm_provider() -> BaseLLMProvider:
    provider_type = settings.LLM_PROVIDER.lower().strip()
    if provider_type == "openai" and settings.LLM_API_KEY:
        return OpenAILLMProvider()
    elif provider_type == "gemini" and settings.LLM_API_KEY:
        return GeminiLLMProvider()
    return MockLLMProvider()
