import io
import pytest
from app.models.meeting import Meeting, TranscriptSegment, Decision, ActionItem

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "ffmpeg" in data
    assert "ai" in data

def test_upload_invalid_file_extension(client):
    file_content = b"fake binary content"
    files = {"file": ("malicious_script.exe", file_content, "application/octet-stream")}
    response = client.post("/api/upload", files=files, data={"auto_process": "false"})
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]

def test_upload_valid_audio_file(client):
    # Minimal WAV file header bytes (44-byte RIFF header)
    riff_wav = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    files = {"file": ("team_sync.wav", riff_wav, "audio/wav")}
    response = client.post(
        "/api/upload",
        files=files,
        data={"title": "Weekly Engineering Sync", "auto_process": "false"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Weekly Engineering Sync"
    assert data["status"] == "uploaded"
    assert "id" in data

def test_list_and_get_meeting_with_intelligence(client, db_session):
    # Seed a test meeting
    meeting = Meeting(
        id="test-meeting-123",
        title="Architecture Discussion",
        original_filename="arch_sync.mp3",
        duration=180.0,
        file_path="./test.wav",
        status="completed",
        summary="Discussed microservices architecture."
    )
    db_session.add(meeting)

    decision = Decision(
        id="dec-1",
        meeting_id="test-meeting-123",
        description="Agreed on GraphQL gateway",
        timestamp=45.0,
        evidence="We agreed to adopt GraphQL gateway.",
        confidence=0.92,
        validation_status="verified"
    )
    db_session.add(decision)

    action = ActionItem(
        id="act-1",
        meeting_id="test-meeting-123",
        task="Document schema contracts",
        owner="Alex",
        deadline="Friday",
        timestamp=60.0,
        evidence="Alex will document schema contracts by Friday.",
        status="pending",
        confidence=0.88,
        validation_status="verified"
    )
    db_session.add(action)
    db_session.commit()

    # 1. List meetings
    list_res = client.get("/api/meetings")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(m["id"] == "test-meeting-123" for m in items)

    # 2. Get detail
    detail_res = client.get("/api/meetings/test-meeting-123")
    assert detail_res.status_code == 200
    d = detail_res.json()
    assert d["title"] == "Architecture Discussion"
    assert len(d["decisions"]) == 1
    assert d["decisions"][0]["validation_status"] == "verified"
    assert len(d["action_items"]) == 1
    assert d["action_items"][0]["owner"] == "Alex"

    # 3. Patch action item status (pending -> completed)
    patch_res = client.patch(
        "/api/meetings/test-meeting-123/actions/act-1",
        json={"status": "completed"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    # 4. Search
    search_res = client.get("/api/search?q=GraphQL")
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["total_matches"] >= 1
    assert any("GraphQL" in r["text"] for r in s_data["results"])

    # 5. Delete meeting
    del_res = client.delete("/api/meetings/test-meeting-123")
    assert del_res.status_code == 204

    # Verify deleted
    get_del = client.get("/api/meetings/test-meeting-123")
    assert get_del.status_code == 404
