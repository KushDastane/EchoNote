from typing import List, Dict, Any, Optional

class SpeakerDiarizationService:
    """
    Modular speaker identification service.
    Keeps timestamps and speaker assignments strictly separate from transcript text.
    Whisper does not provide reliable diarization on its own; this service abstracts
    pyannote/speechbrain integration points and defaults to structured speaker placeholders.
    """

    def __init__(self, is_enabled: bool = False):
        self.is_enabled = is_enabled

    def assign_speakers(
        self,
        segments: List[Dict[str, Any]],
        audio_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Assigns speaker tags to segments.
        If diarization is not configured, provides clearly identified speaker placeholders
        based on conversational turn-taking or 'Speaker 1' / 'Speaker 2' / 'Unknown'.
        """
        if not segments:
            return []

        labeled_segments = []
        current_speaker_idx = 1
        last_end = 0.0

        for i, seg in enumerate(segments):
            # Clone segment dict to avoid mutating original
            item = dict(seg)
            start = item.get("start_time", 0.0)
            
            # Simple acoustic pause heuristic for placeholder speaker alternation
            # If silence gap between turns exceeds 1.5s, alternate placeholder speaker
            if i > 0 and (start - last_end) > 1.8:
                current_speaker_idx = 2 if current_speaker_idx == 1 else 1

            if not item.get("speaker") or item.get("speaker") == "Speaker":
                item["speaker"] = f"Speaker {current_speaker_idx}"

            last_end = item.get("end_time", start)
            labeled_segments.append(item)

        return labeled_segments

speaker_service = SpeakerDiarizationService()
