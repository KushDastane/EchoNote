# EchoNote Architecture & Technical Design

## 1. Executive Summary

**EchoNote** is an evidence-backed meeting intelligence platform designed to transcribe spoken meeting recordings, label conversational turns, synthesize concise executive summaries, and extract confirmed decisions and action items.

The core differentiator of EchoNote is **Evidence-Backed Intelligence**:
Every extracted decision or action item references a supporting transcript excerpt and an exact timestamp. The system cross-examines LLM inferences against the transcript, assigns confidence metrics, and classifies every insight as **Verified**, **Unverified**, or **Flagged**.

---

## 2. System Architecture

```
                       +-----------------------------+
                       |   React 18 + Vite Frontend  |
                       |  (Clean SaaS Dashboard, UI) |
                       +--------------+--------------+
                                      |
                                      | REST APIs (HTTP / JSON / Range Audio)
                                      v
                       +-----------------------------+
                       |      FastAPI Backend        |
                       |  (Endpoints, Routers, CORS) |
                       +--------------+--------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+------------------+         +------------------+         +------------------+
| Audio Service    |         | Transcription    |         | Extraction &     |
| (FFmpeg engine)  |         | (Chunked Whisper |         | Validation       |
| - Format norm    |         |  + Speaker Tag)  |         | (LLM + Engine)   |
+--------+---------+         +--------+---------+         +--------+---------+
         |                            |                            |
         +----------------------------+----------------------------+
                                      |
                                      v
                       +-----------------------------+
                       |     SQLite / PostgreSQL     |
                       |      SQLAlchemy Engine      |
                       +-----------------------------+
```

---

## 3. Ingestion & Audio Pipeline

Long meeting recordings (5–60 minutes, and up to 120 minutes) cannot reliably be converted or transcribed as monolithic in-memory streams. EchoNote executes a multi-stage chunked pipeline:

1. **Validation**:
   - File extension inspection (`.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.webm`, `.mp4`).
   - File size validation (capped at `MAX_UPLOAD_SIZE_MB`, default 250MB).
   - Audio probe inspection via `ffprobe` to determine duration, bitrate, and channels.

2. **Audio Normalization**:
   - Ingested files are converted to uniform 16kHz mono 16-bit PCM WAV using FFmpeg:
     `ffmpeg -y -i input.ext -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav`

3. **Windowed Chunking with Overlap**:
   - The audio is partitioned into time windows (default `AUDIO_CHUNK_LENGTH_SEC = 600` seconds, with `AUDIO_CHUNK_OVERLAP_SEC = 10` seconds).
   - Overlapping windows ensure that words spoken across chunk boundaries are not truncated.

4. **Speech-to-Text & Diarization Architecture**:
   - Audio chunks are transcribed through OpenAI Whisper (`whisper.load_model('base')`).
   - Timestamps from consecutive chunks are merged using cumulative offsets (`offset + segment.start`).
   - Boundary deduplication eliminates redundant segments in the overlap transition.
   - Speaker diarization abstraction assigns speaker turns (`Speaker 1`, `Speaker 2`, etc.), maintaining speaker tags strictly separate from transcript text.

---

## 4. Structured Intelligence & Evidence Verification

```
Transcript Segments -> Structured LLM Extraction -> Evidence Cross-Validation Engine
                                                          |
                      +-----------------------------------+-----------------------------------+
                      |                                   |                                   |
              Exact / High Match                  Partial Sequence                      No Excerpt
             (Similarity >= 0.65)                (0.40 <= Sim < 0.65)               (Sim < 0.40 or None)
                      |                                   |                                   |
                      v                                   v                                   v
             Status: VERIFIED                    Status: UNVERIFIED                  Status: FLAGGED
             Aligned Timestamp                   Preserved Uncertainty               Downweighted Confidence
```

### Prompt Guardrails & Extraction Rules
- **No Hallucinated Owners**: If no specific person or role commits to an action item, the owner is explicitly set to `"Not specified"`.
- **No Invented Deadlines**: If no calendar date or timeframe is stated, deadline is explicitly set to `"Not specified"`.
- **Discussion vs. Decision**: Casual brainstorming or proposals are excluded from the Decisions register unless explicit consensus was reached.
- **Evidence Cross-Checking**: The `EvidenceValidationService` analyzes the excerpt against all transcript segments using sequence matcher ratios and normalized token overlap.

---

## 5. Database Schema & Data Models

- **`Meeting`**:
  - `id`: UUID (Primary Key)
  - `title`: Meeting display title
  - `original_filename`: Source file name
  - `duration`: Float (seconds)
  - `file_path`: Path to uploaded file
  - `processed_file_path`: Path to normalized 16kHz WAV
  - `status`: `uploaded` | `processing` | `completed` | `failed`
  - `summary`: Text summary
  - `key_points`: JSON array of discussion bullets
  - `unresolved_questions`: JSON array of open questions
  - `important_topics`: JSON array of extracted themes
  - `created_at`, `updated_at`: Timestamps

- **`TranscriptSegment`**:
  - `id`: UUID (Primary Key)
  - `meeting_id`: Foreign Key (`meetings.id`, ondelete CASCADE)
  - `start_time`: Float seconds
  - `end_time`: Float seconds
  - `speaker`: String label
  - `text`: Transcript segment text

- **`Decision`**:
  - `id`: UUID (Primary Key)
  - `meeting_id`: Foreign Key (`meetings.id`, ondelete CASCADE)
  - `description`: Decision statement
  - `speaker`: Speaker identifier (nullable)
  - `timestamp`: Float seconds (nullable)
  - `evidence`: Transcript excerpt
  - `confidence`: Float (0.0 to 1.0)
  - `validation_status`: `verified` | `unverified` | `flagged`

- **`ActionItem`**:
  - `id`: UUID (Primary Key)
  - `meeting_id`: Foreign Key (`meetings.id`, ondelete CASCADE)
  - `task`: Actionable task statement
  - `owner`: Assignee ("Not specified" if absent)
  - `deadline`: Target completion ("Not specified" if absent)
  - `timestamp`: Float seconds (nullable)
  - `evidence`: Transcript excerpt
  - `status`: `pending` | `completed`
  - `confidence`: Float (0.0 to 1.0)
  - `validation_status`: `verified` | `unverified` | `flagged`

---

## 6. Frontend Architecture

Built on **React 18** and **Vite** using pure **JavaScript** (no TypeScript) and modular CSS:
- **`Sidebar` & `Header`**: Clean navigation across Overview, Meetings, Upload, Search, and Settings.
- **`AudioPlayer`**: Full-featured audio playback with HTTP Range request streaming, timeline scrub bar, skip buttons, and variable playback speeds.
- **`TranscriptViewer`**: Synchronized transcript highlighting the active segment as audio plays, with search filter and click-to-seek functionality.
- **`DecisionsList` & `ActionItemsList`**: Interactive cards featuring status badges, confidence percentages, and "Jump to timestamp" links that sync audio playback and scroll the transcript directly to the excerpt.
