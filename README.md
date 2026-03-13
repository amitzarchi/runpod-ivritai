# runpod-serverless

[![RunPod](https://api.runpod.io/badge/ivrit-ai/runpod-serverless)](https://www.runpod.io/console/hub/ivrit-ai/runpod-serverless)

A template for quickly deploying an ivrit.ai Speech-to-text API.

Note: if you register at [runpod.io](https://runpod.io), we'd like to ask you to consider using our [referral link](https://runpod.io/?ref=06octndf).
It provides us with credits, which we can then use to provide better services.

## Description

This project provides a serverless solution for transcribing Hebrew audio files. It leverages runpod.io's infrastructure to process audio files efficiently and return transcriptions.
It is part of the [ivrit.ai](https://ivrit.ai) non-profit project.

## API: easy deployment through the Runpod hub

If you simply want to use our models via an API, quick deploy is avaialble via the RunPod hub.

1. Open this template on the hub by clicking [here](https://www.runpod.io/console/hub/ivrit-ai/runpod-serverless).
2. Click the "Deploy" button and create the endpoint.
3. Follow the instructions under the [Usage](#usage) section.

## Contents

- `Dockerfile`: Docker image for the serverless function.
- `app.py`: Minimal FastAPI server (Fireworks/OpenAI compatible).

## Setting up your inference endpoint

1. Log in to [runpod.io]
2. Choose Menu->Serverless
3. Choose New Endpoint
4. Select the desired worker configuration.
   - You can choose the cheapest worker (16GB GPU, $0.00016/second as of August 1st, 2024).
   - Active workers can be 0, max workers is 1 or more.
   - GPUs/worker should be set to 1.
   - **Endpoint type**: Select **Load Balancer** for direct HTTP access.
   - **Model**: Add `ivrit-ai/whisper-large-v3-turbo-ct2` for RunPod model caching (smaller image, faster cold starts).
   - Container image should be set to **yairlifshitz/whisper-runpod-serverless:latest**, or your own Docker image (instruction later on how to build this).
   - Container disk should have at least 20 GB.
5. Click Deploy.

## Usage

Send a JSON body with the audio URL:

```javascript
const response = await fetch("https://YOUR_ENDPOINT_ID.api.runpod.ai/transcribe", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_RUNPOD_API_KEY",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ file: "https://example.com/audio.mp3" }),
});
const result = await response.json();
```

```bash
curl -X POST "https://YOUR_ENDPOINT_ID.api.runpod.ai/transcribe" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"file":"https://example.com/audio.mp3"}'
```

**Endpoints:**
- `GET /ping` — Health check (required by RunPod)
- `POST /transcribe` — Transcribe remote audio (JSON body: `{"file": "URL"}`)

**Response:** `verbose_json` format with `text`, `language`, `duration`, `segments` (with word-level timestamps).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
Patreon link: [here](https://www.patreon.com/ivrit_ai).

## License

Our code and model are released under the MIT license.

## Acknowledgements

- [Our long list of data contributors](https://www.ivrit.ai/en/credits)
- Our data annotation volunteers!
