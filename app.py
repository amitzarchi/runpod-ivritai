"""
FastAPI server for ivrit.ai speech-to-text.
Designed for RunPod Load Balancer endpoints.
"""
import dataclasses
import types
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import ivrit

# Maximum size for grouped arrays (in characters)
MAX_SEGMENT_GROUP_SIZE = 500000

# Global variable to track the currently loaded model
current_model = None

app = FastAPI(title="ivrit.ai Speech-to-Text API")


# --- Request/Response models ---
class TranscribeArgs(BaseModel):
    url: str | None = None
    blob: str | None = None  # base64-encoded audio
    language: str = "he"
    diarize: bool = False
    verbose: bool = False

    class Config:
        extra = "allow"  # Allow extra fields passed to ivrit.transcribe()


class TranscribeRequest(BaseModel):
    model: str = Field(..., description="Model name, e.g. ivrit-ai/whisper-large-v3-turbo-ct2")
    engine: str = Field(default="faster-whisper", description="faster-whisper or stable-whisper")
    streaming: bool = Field(default=False, description="Stream results incrementally")
    transcribe_args: TranscribeArgs = Field(..., description="Transcription parameters")


def transcribe_core(engine: str, model_name: str, transcribe_args: dict):
    """Core transcription logic - yields segment groups."""
    global current_model

    different_model = (
        not current_model
        or current_model.engine != engine
        or current_model.model != model_name
    )

    if different_model:
        print(f"Loading new model: {engine} with {model_name}")
        current_model = ivrit.load_model(
            engine=engine, model=model_name, local_files_only=True
        )
    else:
        print(f"Reusing existing model: {engine} with {model_name}")

    args = transcribe_args.copy()
    diarize = args.get("diarize", False)

    if diarize:
        res = current_model.transcribe(**args)
        segs = res["segments"]
    else:
        args["stream"] = True
        segs = current_model.transcribe(**args)

    if isinstance(segs, types.GeneratorType):
        for s in segs:
            yield [dataclasses.asdict(s)]
    else:
        current_group = []
        current_size = 0

        for s in segs:
            seg_dict = dataclasses.asdict(s)
            seg_size = len(str(seg_dict))

            if current_group and (current_size + seg_size > MAX_SEGMENT_GROUP_SIZE):
                yield current_group
                current_group = []
                current_size = 0

            current_group.append(seg_dict)
            current_size += seg_size

        if current_group:
            yield current_group


# --- Endpoints ---

@app.get("/ping")
async def health_check():
    """Health check - required by RunPod Load Balancer."""
    return {"status": "healthy"}


@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    """
    Transcribe audio from URL or base64 blob.
    """
    if request.engine not in ("faster-whisper", "stable-whisper"):
        raise HTTPException(
            status_code=400,
            detail=f"engine must be 'faster-whisper' or 'stable-whisper', got '{request.engine}'",
        )

    args = request.transcribe_args.model_dump(exclude_none=True)
    if not args.get("url") and not args.get("blob"):
        raise HTTPException(
            status_code=400,
            detail="transcribe_args must contain either 'url' or 'blob'",
        )

    try:
        stream_gen = transcribe_core(
            request.engine, request.model, args
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if request.streaming:
        from fastapi.responses import StreamingResponse
        import json

        async def generate():
            for group in stream_gen:
                yield json.dumps(group) + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
        )

    # Non-streaming: collect all segments
    result = []
    for group in stream_gen:
        result.extend(group)

    return {"result": result}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "80"))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
