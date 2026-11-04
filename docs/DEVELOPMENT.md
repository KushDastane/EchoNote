# EchoNote Development Guide

## 1. Prerequisites

- **Python**: 3.10 to 3.14 (64-bit)
- **Node.js**: v18 or higher (v24.15+ verified)
- **npm**: v9 or higher
- **FFmpeg & FFprobe**: Installed and accessible in PATH or via Windows winget package (`Gyan.FFmpeg`).

---

## 2. Local Environment Setup

### Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *Note: In development, `LLM_PROVIDER=mock` runs locally without requiring paid API credits. To use OpenAI or Gemini, set `LLM_PROVIDER=openai` or `LLM_PROVIDER=gemini` and set `LLM_API_KEY`.*

5. Start the backend development server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at `http://127.0.0.1:8000`.
   Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

### Frontend Setup

1. In a separate terminal, navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend application will run at `http://localhost:5173`.
   Vite proxies `/api` calls directly to the FastAPI server at `http://127.0.0.1:8000`.

---

## 3. Running the Test Suite

### Backend Pytest Suite

Run all automated unit and integration tests:
```bash
# From the project root or backend directory
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -v
```

The test suite covers:
- System health checks and dependency probing (`test_api.py::test_health_check_endpoint`)
- Rejection of invalid file types and oversized payloads (`test_api.py::test_upload_invalid_file_extension`)
- Valid audio ingestion and database row creation (`test_api.py::test_upload_valid_audio_file`)
- Meeting retrieval, action item status updates, and search (`test_api.py::test_list_and_get_meeting_with_intelligence`)
- Audio chunk window calculations and window offsets (`test_audio_chunking.py::test_compute_chunk_windows_*`)
- Segment deduplication across overlap boundaries (`test_audio_chunking.py::test_merge_chunk_segments_offset_and_deduplication`)
- Strict Pydantic schema validation (`test_llm_schemas.py::test_llm_extraction_result_pydantic_validation`)
- Enforcing `"Not specified"` for missing owners/deadlines (`test_llm_schemas.py::test_action_item_schema_defaults_not_specified`)
- Transcript evidence matching and flagging (`test_validation.py::*`)

### Frontend Build Verification

Verify that the frontend builds without errors:
```bash
cd frontend
npm run build
```

---

## 4. Audio Engine & FFmpeg Troubleshooting

- **FFmpeg Auto-Detection**: EchoNote automatically inspects your system `PATH` and Windows Winget package directories (`%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg...`).
- If FFmpeg is installed in a custom location, explicitly define its path in `backend/.env`:
  ```ini
  FFMPEG_PATH=C:/tools/ffmpeg/bin/ffmpeg.exe
  FFPROBE_PATH=C:/tools/ffmpeg/bin/ffprobe.exe
  ```

---

## 5. Security & Deployment Best Practices

- Never commit `.env` files or API credentials to version control.
- Ensure `UPLOAD_DIR` and `PROCESSED_DIR` are located on drives with adequate storage.
- Audio streaming uses HTTP 206 Partial Content range headers for smooth scrubbing in the frontend audio player.
