# EchoNote

EchoNote turns meeting recordings into searchable transcripts and structured meeting notes. Its focus is **evidence-backed insights**: decisions and action items include transcript evidence and timestamps, with validation status shown in the app.

## What it does

- Uploads audio recordings (up to 250 MB by default) and tracks processing progress.
- Normalizes audio with FFmpeg, splits long recordings into overlapping chunks, and transcribes speech with OpenAI Whisper.
- Produces meeting summaries, key points, decisions, action items, topics, and unresolved questions.
- Associates extracted decisions and actions with transcript excerpts, timestamps, confidence, and a validation status.
- Provides a synchronized audio player, transcript navigation, action-item status updates, dashboard metrics, and search across meetings.
- Uses a local heuristic provider by default, or can send transcripts to OpenAI or Google Gemini for structured extraction.

> **Note:** Evidence validation helps reviewers assess extracted insights; it does not guarantee their correctness. The default `mock` LLM provider uses keyword heuristics, not a language model. Review generated content before relying on it.

## Technology

- **Frontend:** React 18, Vite, JavaScript
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy
- **Storage:** SQLite by default
- **Audio:** FFmpeg/FFprobe and OpenAI Whisper
- **Extraction:** Mock provider, OpenAI, or Google Gemini

## Requirements

- Python 3.10 or later
- Node.js 18 or later and npm
- FFmpeg and FFprobe available on `PATH` (or configured explicitly)
- For transcription, a working installation of `openai-whisper` and its PyTorch dependencies. The first run may download the selected Whisper model and requires additional disk space.

## Quick start

### 1. Set up the backend

From the project root, open a terminal:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell prevents virtual-environment activation, either allow activation for your user or run the commands below using `backend\.venv\Scripts\python.exe` directly.

Start the API from the `backend` directory:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API is at `http://127.0.0.1:8000`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 2. Set up the frontend

In a second terminal, from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). Vite proxies `/api` requests to the local backend.

### Windows helper scripts

After installing backend dependencies into `backend\.venv` and frontend dependencies with `npm install`, the project-root scripts can start the services:

```powershell
.\run-backend.ps1
.\run-frontend.bat
```

Alternatively, use `run-backend.bat`. Start the backend and frontend in separate terminals.

## Configuration

Backend settings are read from `backend/.env`; begin with the tracked template at `backend/.env.example`. The default configuration is suitable for local development and does not require an LLM API key.

| Variable | Default | Description |
|---|---|---|
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Backend bind address and port |
| `CORS_ORIGINS` | Local Vite origins | Comma-separated allowed browser origins |
| `DATABASE_URL` | SQLite database | SQLAlchemy database connection URL |
| `UPLOAD_DIR` / `PROCESSED_DIR` | `./uploads` / `./processed` | Original and normalized audio storage |
| `MAX_UPLOAD_SIZE_MB` | `250` | Maximum accepted upload size |
| `FFMPEG_PATH` / `FFPROBE_PATH` | Auto-detected | Set these if the binaries are not on `PATH` |
| `WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `WHISPER_DEVICE` | `cpu` | Whisper inference device |
| `LLM_PROVIDER` | `mock` | `mock`, `openai`, or `gemini` |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `LLM_API_KEY` | Empty | API key when using a hosted LLM provider |
| `AUDIO_CHUNK_LENGTH_SEC` / `AUDIO_CHUNK_OVERLAP_SEC` | `600` / `10` | Audio chunk duration and overlap |

To use a hosted provider, set `LLM_PROVIDER` and `LLM_API_KEY` in `backend/.env`. For Gemini, set `LLM_MODEL` to the desired Gemini model as well. Never commit `.env` files or API keys.

## API overview

- `GET /api/health` — backend, database, audio-tool, and AI configuration status
- `POST /api/upload` — upload a recording
- `POST /api/process/{meeting_id}` and `GET /api/status/{meeting_id}` — start processing and check progress
- `GET /api/meetings` and `GET /api/meetings/{meeting_id}` — list and retrieve meetings
- `GET /api/meetings/metrics` — dashboard metrics
- `GET /api/meetings/{meeting_id}/audio` — stream meeting audio
- `PATCH /api/meetings/{meeting_id}/actions/{action_id}` — update an action item
- `DELETE /api/meetings/{meeting_id}` — delete a meeting
- `GET /api/search?q={term}` — search meeting content

See the interactive Swagger UI at `/docs` for request fields and response schemas.

## Tests and build

Run backend tests from the project root:

```powershell
python -m pytest backend\tests -v
```

Build the frontend:

```powershell
cd frontend
npm run build
```

## Project layout

```text
backend/
  app/                 FastAPI routes, models, schemas, and services
  tests/               Backend tests
  requirements.txt
frontend/
  src/                 React pages, components, API client, and styles
  package.json
docs/
  ARCHITECTURE.md      System architecture and processing details
  DEVELOPMENT.md       Development setup and troubleshooting
```

For more detail, see [the architecture guide](docs/ARCHITECTURE.md) and [the development guide](docs/DEVELOPMENT.md).
