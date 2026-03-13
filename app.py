"""
Minimal ivrit.ai speech-to-text API.
POST /transcribe with form field: file (URL to remote audio).
Returns verbose_json with word and segment timestamps.
"""
import os

from fastapi import FastAPI, Form, HTTPException

import ivrit

HF_CACHE_ROOT = "/runpod-volume/huggingface-cache/hub"
MODEL_ID = "ivrit-ai/whisper-large-v3-turbo-ct2"
current_model = None

app = FastAPI(title="ivrit.ai Whisper API")


def resolve_cached_model_path(model_id: str) -> str | None:
    if "/" not in model_id:
        return None
    org, name = model_id.split("/", 1)
    model_root = os.path.join(HF_CACHE_ROOT, f"models--{org}--{name}")
    snapshots_dir = os.path.join(model_root, "snapshots")
    if not os.path.isdir(snapshots_dir):
        return None
    refs_main = os.path.join(model_root, "refs", "main")
    if os.path.isfile(refs_main):
        with open(refs_main) as f:
            h = f.read().strip()
        path = os.path.join(snapshots_dir, h)
        if os.path.isdir(path):
            return path
    versions = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
    return os.path.join(snapshots_dir, sorted(versions)[-1]) if versions else None


def load_model():
    global current_model
    if current_model is not None:
        return current_model
    path = resolve_cached_model_path(MODEL_ID)
    if path:
        os.environ["HF_HUB_OFFLINE"] = "1"
        try:
            current_model = ivrit.load_model(engine="faster-whisper", model=path, local_files_only=True)
        finally:
            os.environ.pop("HF_HUB_OFFLINE", None)
    else:
        current_model = ivrit.load_model(engine="faster-whisper", model=MODEL_ID, local_files_only=True)
    return current_model


@app.get("/ping")
async def health_check():
    return {"status": "healthy"}


@app.post("/transcribe")
async def transcribe(file: str = Form()):
    """file: URL to remote audio (e.g. https://example.com/audio.mp3)"""
    if not file or not file.startswith(("http://", "https://")):
        raise HTTPException(400, "file must be a URL (http:// or https://)")
    model_obj = load_model()
    result = model_obj.transcribe(
        url=file,
        language="he",
        stream=False,
        word_timestamps=True,
    )
    segments = result["segments"]
    text = " ".join(s.text for s in segments)
    duration = segments[-1].end if segments else 0.0
    out_segments = []
    for i, s in enumerate(segments):
        seg = {"id": i, "start": s.start, "end": s.end, "text": s.text}
        words = None
        if hasattr(s, "words") and s.words:
            words = [{"word": w.word, "start": w.start, "end": w.end} for w in s.words]
        elif getattr(s, "extra_data", None):
            words = [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in (s.extra_data.get("words") or [])]
        if words:
            seg["words"] = words
        out_segments.append(seg)
    return {
        "text": text,
        "language": "he",
        "duration": duration,
        "task": "transcribe",
        "segments": out_segments,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "80"))
    uvicorn.run(app, host="0.0.0.0", port=port)
