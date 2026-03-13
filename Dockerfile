# Include Python
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

# Define your working directory
WORKDIR /

# Configure LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH="/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib:/opt/conda/lib/python3.11/site-packages/nvidia/cublas/lib"

# Install relevant packages 
RUN apt update
RUN apt install -y ffmpeg

# Install python packages
# ivrit with faster-whisper only (no pyannote/speechbrain for diarization)
RUN pip3 install "ivrit[faster-whisper]==0.1.8" torch==2.4.1 huggingface-hub==0.36.0 fastapi uvicorn

# Models are loaded from RunPod model cache (configure ivrit-ai/whisper-large-v3-turbo-ct2 in endpoint settings)
# No model pre-download - keeps image small for faster container startup

ADD app.py .

# Expose port for Load Balancer
EXPOSE 80

# Start FastAPI server (Load Balancer endpoint)
CMD [ "python", "-u", "/app.py" ]

