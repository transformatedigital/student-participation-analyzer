from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Clase Analytics API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try multiple paths for data directory
_paths = [
    Path("/app/data/clases"),  # Docker
    Path(__file__).parent.parent / "data" / "clases",  # Local
]
DATA_DIR = None
for p in _paths:
    if p.exists():
        DATA_DIR = p
        break
if DATA_DIR is None:
    DATA_DIR = _paths[0]  # Default to first path even if it doesn't exist


@app.get("/api/clases")
async def list_classes():
    """List all class sessions."""
    classes = []
    for session_dir in DATA_DIR.glob("*"):
        if session_dir.is_dir():
            metadata_file = session_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    classes.append(metadata)

    return {"classes": sorted(classes, key=lambda x: x["date"], reverse=True)}


@app.get("/api/clases/{session_id}")
async def get_session(session_id: str):
    """Get session metadata and overview data."""
    session_dir = DATA_DIR / session_id
    metadata_file = session_dir / "metadata.json"
    speakers_file = session_dir / "speakers.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(metadata_file) as f:
        metadata = json.load(f)

    speakers_data = {}
    if speakers_file.exists():
        with open(speakers_file) as f:
            speakers_data = json.load(f)

    return {
        "metadata": metadata,
        "speakers": speakers_data.get("speakers", [])
    }


@app.get("/api/clases/{session_id}/transcripcion")
async def get_transcription(session_id: str):
    """Get full transcription with segments."""
    session_dir = DATA_DIR / session_id
    analysis_file = session_dir / "analysis.json"

    if not analysis_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(analysis_file) as f:
        analysis = json.load(f)

    # Prefer new format (full_transcription), fall back to old format (sample_transcription)
    segments = analysis.get("full_transcription") or analysis.get("sample_transcription", [])

    # If using old format, apply speaker name mapping
    if not analysis.get("full_transcription") and segments:
        speakers_file = session_dir / "speakers.json"
        speakers_map = {}
        if speakers_file.exists():
            with open(speakers_file) as f:
                speakers_data = json.load(f)
                for speaker in speakers_data.get("speakers", []):
                    speakers_map[speaker["id"]] = speaker["name"]

        for segment in segments:
            speaker_id = None
            for key, name in [
                ("speaker_1", "Teacher"),
                ("speaker_2", "Student 1"),
                ("speaker_3", "Student 2"),
                ("speaker_4", "Student 3"),
                ("speaker_5", "Student 4")
            ]:
                if segment.get("speaker") == name:
                    speaker_id = key
                    break

            if speaker_id and speaker_id in speakers_map:
                segment["speaker_name"] = speakers_map[speaker_id]

    return {
        "total_segments": len(segments),
        "segments": segments
    }


@app.get("/api/clases/{session_id}/participacion")
async def get_participation(session_id: str):
    """Get participation analysis (questions, responses, per-student summary)."""
    session_dir = DATA_DIR / session_id
    analysis_file = session_dir / "analysis.json"

    if not analysis_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(analysis_file) as f:
        analysis = json.load(f)

    # Support both new and old data formats
    teacher_questions = analysis.get("teacher_questions", []) or analysis.get("teacher_questions_full", [])
    student_contributions = analysis.get("student_contributions", []) or analysis.get("student_contributions_full", [])

    # Normalize field names for new format (timestamp -> timestamp_start)
    normalized_questions = []
    for q in teacher_questions:
        normalized = dict(q)
        if 'timestamp' in normalized and 'timestamp_start' not in normalized:
            normalized['timestamp_start'] = normalized.pop('timestamp')
        if 'directed_to' in normalized and 'speaker' not in normalized:
            normalized['speaker'] = normalized.get('directed_to')
        normalized_questions.append(normalized)

    normalized_contributions = []
    for c in student_contributions:
        normalized = dict(c)
        if 'timestamp' in normalized and 'timestamp_start' not in normalized:
            normalized['timestamp_start'] = normalized.pop('timestamp')
        normalized_contributions.append(normalized)

    # Normalize per_student_summary field names
    summary = analysis.get("per_student_summary", {})
    normalized_summary = {}
    for student, data in summary.items():
        normalized_data = dict(data)
        # Map responses_to_teacher to responses_count if needed
        if 'responses_to_teacher' in normalized_data and 'responses_count' not in normalized_data:
            normalized_data['responses_count'] = normalized_data.get('responses_to_teacher', 0)
        normalized_summary[student] = normalized_data

    return {
        "teacher_questions": normalized_questions,
        "student_contributions": normalized_contributions,
        "per_student_summary": normalized_summary,
        # Backward compatibility
        "student_questions": analysis.get("student_questions", []),
        "evaluation_frameworks": analysis.get("evaluation_frameworks", {})
    }


@app.get("/api/clases/{session_id}/timeline")
async def get_timeline(session_id: str):
    """Get participation timeline and full transcription."""
    session_dir = DATA_DIR / session_id
    analysis_file = session_dir / "analysis.json"

    if not analysis_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(analysis_file) as f:
        analysis = json.load(f)

    return {
        "participation_timeline": analysis.get("participation_timeline", []),
        "full_transcription": analysis.get("full_transcription", [])
    }


@app.get("/api/clases/{session_id}/evaluacion")
async def get_evaluation(session_id: str):
    """Get evaluation report with frameworks."""
    session_dir = DATA_DIR / session_id
    analysis_file = session_dir / "analysis.json"

    if not analysis_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(analysis_file) as f:
        analysis = json.load(f)

    return {
        "evaluation_frameworks": analysis.get("evaluation_frameworks", {}),
        "student_questions": analysis.get("student_questions", [])
    }


@app.get("/api/clases/{session_id}/hablantes")
async def get_speakers(session_id: str):
    """Get speaker profiles."""
    session_dir = DATA_DIR / session_id
    speakers_file = session_dir / "speakers.json"

    if not speakers_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(speakers_file) as f:
        speakers_data = json.load(f)

    return speakers_data


@app.post("/api/clases/{session_id}/speakers/{speaker_id}")
async def update_speaker(session_id: str, speaker_id: str, data: dict):
    """Update speaker information (name, degree, nationality, email)."""
    session_dir = DATA_DIR / session_id
    speakers_file = session_dir / "speakers.json"

    if not speakers_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    with open(speakers_file) as f:
        speakers_data = json.load(f)

    for speaker in speakers_data.get("speakers", []):
        if speaker.get("id") == speaker_id:
            speaker.update(data)
            break

    with open(speakers_file, "w") as f:
        json.dump(speakers_data, f, indent=2)

    return speakers_data


@app.get("/api/clases/{session_id}/audio_clips")
async def list_audio_clips(session_id: str):
    """List available audio clips for speaker identification."""
    session_dir = DATA_DIR / session_id
    audio_clips_dir = session_dir / "audio_clips"
    metadata_file = session_dir / "speaker_clips_metadata.json"

    if not audio_clips_dir.exists():
        return {"clips": []}

    # Load metadata if available
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file) as f:
            meta_data = json.load(f)
            for clip_info in meta_data.get("speaker_clips_info", []):
                metadata[clip_info["id"]] = clip_info
            for clip_info in meta_data.get("student2_clips", []):
                metadata[clip_info["id"]] = clip_info

    clips = []
    for clip_file in sorted(audio_clips_dir.glob("*.mp3")):
        clip_id = clip_file.stem
        clip_info = metadata.get(clip_id, {})

        is_student = "student" in clip_id.lower() or "aryang" in clip_info.get("note", "").lower()
        is_unknown = "unknown" in clip_info.get("estimated_speaker", "").lower()

        clips.append({
            "id": clip_id,
            "filename": clip_file.name,
            "url": f"/api/clases/{session_id}/audio_clips/{clip_file.name}",
            "speaker": clip_info.get("estimated_speaker", "Unknown"),
            "note": clip_info.get("note", ""),
            "is_student": is_student,
            "is_unknown": is_unknown
        })

    return {"clips": clips}


@app.get("/api/clases/{session_id}/audio_clips/{clip_filename}")
async def get_audio_clip(session_id: str, clip_filename: str):
    """Stream audio clip file."""
    session_dir = DATA_DIR / session_id
    clip_path = session_dir / "audio_clips" / clip_filename

    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Audio clip not found")

    return FileResponse(
        path=clip_path,
        media_type="audio/mpeg",
        filename=clip_filename
    )


@app.get("/api/clases/{session_id}/voice_training_clips")
async def list_voice_training_clips(session_id: str):
    """List voice training clips for speaker verification."""
    session_dir = DATA_DIR / session_id
    clips_dir = session_dir / "voice_training_clips"
    metadata_file = clips_dir / "voice_clips_metadata.json"

    if not clips_dir.exists():
        return {"clips": []}

    clips = []
    if metadata_file.exists():
        with open(metadata_file) as f:
            meta_data = json.load(f)
            for clip_info in meta_data.get("voice_training_clips", []):
                clips.append({
                    "id": clip_info["id"],
                    "filename": clip_info["filename"],
                    "url": f"/api/clases/{session_id}/voice_training_clips/{clip_info['filename']}",
                    "speaker_estimated": clip_info["speaker_estimated"],
                    "timestamp_start": clip_info["timestamp_start"],
                    "duration_seconds": clip_info["duration_seconds"],
                    "note": clip_info["note"]
                })

    return {"clips": clips}


@app.get("/api/clases/{session_id}/voice_training_clips/{clip_filename}")
async def get_voice_training_clip(session_id: str, clip_filename: str):
    """Stream voice training clip file."""
    session_dir = DATA_DIR / session_id
    clip_path = session_dir / "voice_training_clips" / clip_filename

    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Voice clip not found")

    return FileResponse(
        path=clip_path,
        media_type="audio/aac",
        filename=clip_filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )


@app.post("/api/clases/{session_id}/voice_training_clips/{clip_id}/verify")
async def verify_voice_clip(session_id: str, clip_id: str, data: dict):
    """Verify and label a voice training clip."""
    session_dir = DATA_DIR / session_id
    clips_dir = session_dir / "voice_training_clips"
    metadata_file = clips_dir / "voice_clips_metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Metadata file not found")

    with open(metadata_file) as f:
        metadata = json.load(f)

    # Update clip info
    updated = False
    for clip_info in metadata.get("voice_training_clips", []):
        if clip_info["id"] == clip_id:
            clip_info["speaker_verified"] = data.get("speaker_verified")
            clip_info["verified_by_user"] = True
            clip_info["verification_note"] = data.get("note", "")
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Clip not found")

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return {"success": True, "clip_id": clip_id}


@app.post("/api/clases/{session_id}/audio_clips/{clip_id}/label")
async def label_audio_clip(session_id: str, clip_id: str, data: dict):
    """Label/identify an audio clip (e.g., assign to a speaker)."""
    session_dir = DATA_DIR / session_id
    metadata_file = session_dir / "speaker_clips_metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Metadata file not found")

    with open(metadata_file) as f:
        metadata = json.load(f)

    # Update clip info in speaker_clips_info
    updated = False
    for clip_info in metadata.get("speaker_clips_info", []):
        if clip_info["id"] == clip_id:
            clip_info.update(data)
            updated = True
            break

    # Also check student2_clips if not found
    if not updated:
        for clip_info in metadata.get("student2_clips", []):
            if clip_info["id"] == clip_id:
                clip_info.update(data)
                updated = True
                break

    if not updated:
        raise HTTPException(status_code=404, detail="Clip not found")

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    return {"success": True, "clip_id": clip_id, "updated": data}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
