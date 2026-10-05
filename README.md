# SiteLens AI

SiteLens AI is a construction-site safety platform with an Android field client and two FastAPI services:

- A FastAPI hazard orchestration service for image analysis, live frame streaming, SOP retrieval, voice queries, alerts, and audit records.
- A database-backed FastAPI application used by the Android field-worker app and its mobile/glasses sessions.
- An Android app that captures phone-camera frames, exchanges glasses telemetry over WebSocket/Bluetooth, records voice input, and reads assistant responses aloud.

The repository also contains a standalone browser UI served by the hazard orchestration service at `/`.

## Capabilities

- Single-image construction hazard detection with severity, recommended actions, processing metadata, and SOP references.
- Live base64 frame processing over WebSocket.
- VLM backends for Ollama, Grok, Groq, or local Transformers configuration.
- Retrieval-augmented safety guidance over the SOP files in `data/sops/` using sentence-transformers and FAISS.
- Voice transcription and voice-to-SOP querying through Groq Whisper when configured.
- Rule-engine decisions and safeguards around generated alerts.
- Alert history, Server-Sent Events, escalation, incident history, compliance summaries, and CSV export.
- Mobile/glasses sessions, events, image uploads, reports, tasks, sites, and users.
- Multilingual assistant responses and Android text-to-speech support.
- Optional YOLO integration when the package and model are installed.

## Repository Layout

```text
app/                 Hazard orchestration API, RAG pipeline, static browser UI
backend/             Database and mobile/glasses API
mobile/              Android field-worker and smart-glasses companion
data/sops/           Safety procedure Markdown files
 data/faiss_index/   Checked-in FAISS index and metadata
pyproject.toml       Project metadata; Python >= 3.12
```

## Prerequisites

- Python 3.12 or newer.
- Android Studio with an Android SDK for the mobile app.
- A VLM provider for image analysis. The service can start without one, but detection returns an unavailable response until a provider is configured.
- A Groq API key for Groq VLM or Whisper features, or an Ollama installation for local inference.

The Python dependencies are currently listed in `backend/requirements.txt`. `pyproject.toml` contains project metadata but does not declare runtime dependencies.

## Project Setup
### 1. Python Installation
From the repository root on Windows PowerShell:

```bash
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` and use `data/sops` paths with forward slashes.

### 2. Environment (.env) Setup
```bash
cp .env.example .env
```

### 3. Backend Setup
Open a new terminal (backend)

```powershell
Set-Location backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Backend runs at http://localhost:8000


### 4. VLM Setup
Open a new terminal (VLM)

```powershell
Set-Location C:\Users\MONIKA\OneDrive\Desktop\SiteLensAI
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8001
```
VLM runs at http://localhost:8001


### 5. Mobile Setup
1. Open `\mobile` folder in Android Studio
2. Turn `ON` developer mode in any android mobile with version >= 11
3. 

1.
Android Emulator (Default):
◦
http://10.0.2.2:8000
◦
Note: 10.0.2.2 is the special alias used by the Android emulator to reach localhost (127.0.0.1) on your development machine.
2.
Physical Android Device (USB / Local Wi-Fi):
◦
http://<YOUR_COMPUTER_LOCAL_IP>:8000 (e.g., http://192.168.1.50:8000)
◦
Note: Your PC and physical phone must be connected to the same Wi-Fi network, and you should use your computer's local IPv4 address (found via ipconfig on Windows or ifconfig on macOS/Linux).

## Configuration

Create a `.env` file in the repository root. Values not supplied use the defaults in `app/config.py` and `backend/utils/config.py`.

### Hazard/RAG service

| Variable | Default | Purpose |
| --- | --- | --- |
| `VLM_BACKEND` | `grok` | Configured backend enum: `ollama`, `grok`, `groq`, or `transformers`. |
| `GROK_API_KEY` | unset | xAI vision API credential. |
| `GROK_MODEL` | `grok-2-vision-latest` | xAI model name. |
| `GROQ_API_KEY` | unset | Groq VLM and Whisper credential. |
| `GROQ_MODEL` | `qwen/qwen3.6-27b` | Groq model name. |
| `GROQ_STT_MODEL` | `whisper-large-v3-turbo` | Groq speech-to-text model name. |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL. |
| `OLLAMA_MODEL` | `qwen2.5vl` | Ollama vision model. |
| `VECTOR_BACKEND` | `faiss` | Vector store backend: `faiss` or `supabase`. |
| `FAISS_INDEX_PATH` | `data/faiss_index` | FAISS index directory. |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers embedding model. |
| `YOLO_ENABLED` | `false` | Enables optional YOLO support. |
| `YOLO_MODEL` | `yolo11n.pt` | YOLO model path/name. |
| `FRAME_SKIP` | `3` | Process every Nth streamed frame. |

Set `VLM_BACKEND=groq` when using `GROQ_API_KEY`; otherwise the hazard service defaults to `grok`.

For Supabase vector storage, also configure `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`. The current implementation initializes FAISS by default and auto-ingests `data/sops/` if the index is empty.

### Database backend

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///sitelens.db` | SQLAlchemy database URL. PostgreSQL can be used with `psycopg2-binary`. |
Do not commit `.env`, API keys, generated uploads, or local database files.

## Running the Services

There are two independent FastAPI applications. They both default to port 8000, so run them on different ports when both are needed.

The database/mobile application entry point is `backend/main.py`, and the separate hazard/RAG application entry point is `app/main.py`.

### 1. Database backend

This service creates the configured database schema and seeds default data during startup. With no `DATABASE_URL`, it creates a local `sitelens.db` SQLite database in `backend/` when started from that directory.

```powershell
Set-Location backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend is then available at:

- Root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`

### 2. Hazard, RAG, voice, and audit service

Start this service from the repository root. Use port 8001 if the database backend is already using 8000.

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

The static hazard-detection UI is at `http://localhost:8001/`; API docs are at `http://localhost:8001/docs`; health information is at `http://localhost:8001/health`.

On startup, this service initializes the VLM, FAISS retriever, STT engine, rule engine, and audit database independently. A failed optional component is logged and the service continues with a fallback where supported.

## SOP Ingestion

The hazard service auto-ingests the SOP directory when the FAISS index is empty. To rebuild or populate an index manually:

```powershell
python -m app.rag.ingest
python -m app.rag.ingest --directory data/sops --chunk-size 500 --overlap 50 --store-path data/faiss_index
```

Supported source files are `.md` and `.txt`. The checked-in index is under `data/faiss_index/`.

## API Overview

### Hazard/RAG service

- `POST /api/detect` - Analyze a multipart image or base64 image; optionally include `worker_query`.
- `GET /api/alerts` - Read recent in-memory alerts, with optional `limit` and `severity` filters.
- `GET /api/alerts/stream` - Subscribe to alert updates using Server-Sent Events.
- `POST /api/alerts/escalate` - Manually escalate an alert by `alert_id`.
- `POST /api/query` - Retrieve SOP guidance for a text query.
- `POST /api/voice/transcribe` - Transcribe an uploaded audio file.
- `POST /api/voice/query` - Transcribe audio and retrieve related SOP guidance.
- `GET /api/audit/incidents` - List persisted incidents with filters.
- `GET /api/audit/incidents/{incident_id}` - Read one incident.
- `GET /api/audit/report` - Generate a compliance summary.
- `GET /api/audit/export` - Export incidents as CSV.
- `WS /ws/stream` - Stream base64 frames and receive hazard alerts.

For the WebSocket protocol, send `{"frame":"<base64>"}`, `{"type":"query","text":"..."}`, or `{"type":"ping"}`. See `/docs` for request and response schemas.

### Database backend

- `POST /api/auth/login` and `POST /api/users/create` - User authentication and creation.
- `GET /api/sites` - List sites.
- `GET /api/tasks/{user_id}` - List tasks for a user.
- `POST /api/sessions/start` - Start a worker or glasses session.
- `POST /api/sessions/{session_id}/stop` - Complete a session.
- `GET /api/sessions/{session_id}/events` - List session telemetry.
- `POST /api/sessions/{session_id}/events` - Store a telemetry event.
- `POST /api/analyze` - Analyze an uploaded image through the configured AI companion service.
- `POST /api/sessions/{session_id}/upload-frame` - Upload and analyze a session frame.
- `WS /ws/glasses/{session_id}` - Receive live glasses events and return reports and assistant messages.
- `GET /api/sessions/{session_id}/reports/latest` - Read the latest session report.
- `POST /api/sessions/{session_id}/reports/generate` - Generate a report.
- `GET /api/reports` - List reports.

The complete, generated request and response schemas are available at each service's `/docs` endpoint.

## Backend-Mobile-VLM Sync

The Android app and database backend are connected end to end through the following flow:

1. Android calls `POST /api/sessions/start` and stores the returned session ID.
2. Android uploads phone-camera JPEG frames to `POST /api/sessions/{session_id}/upload-frame`.
3. The backend stores the image, calls `backend/services/ai_service.py`, and returns an event whose `camera_observation` contains the analysis and whose metadata contains the severity and recommended actions.
4. For live glasses or telemetry mode, Android connects to `WS /ws/glasses/{session_id}`. Each JSON event is persisted, analyzed by the same AI companion service, and acknowledged with an event, report, and optional assistant message.
5. Android converts assistant messages to speech and can stop the session through `POST /api/sessions/{session_id}/stop`.

This path is contract-compatible in the source: the Android client uses the same routes, field names, and response models defined by `backend/routes/mobile.py` and `backend/models.py`.

The separate `app/` service is not automatically called by the database backend or Android app. It has its own VLM, FAISS/SOP, STT, rule-engine, audit, and streaming stack. Running both services does not connect their pipelines; use the database backend's configured `GROQ_API_KEY`, `GROK_API_KEY`, `OPENAI_API_KEY`, or `OLLAMA_HOST` for the Android/mobile VLM path.

### Minimal integration test

Start the database backend on port 8000, configure a valid VLM provider, and run the Android app with its default emulator URL `http://10.0.2.2:8000`. A physical device must use the computer's LAN address instead. Then verify:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/docs
```

Start a session from the app, capture a frame, and confirm that the app receives a non-empty `analysis`, `severity`, or `assistant_message`. For glasses mode, confirm the WebSocket status reaches `Connected to glasses stream` and that a sent event receives `status: received`.

## Android App

The Android module uses Kotlin, Jetpack Compose, CameraX, OkHttp, Gson, coroutines, and Bluetooth GATT support. It includes phone-camera capture, demo/live sessions, session telemetry, voice input, text-to-speech, and configurable BLE glasses connectivity.

The debug build uses `http://10.0.2.2:8000` as its default backend URL, which points an Android emulator at the host machine. A physical device needs a host-reachable address such as `http://192.168.x.x:8000`; update `DEFAULT_BACKEND_URL` in `mobile/app/build.gradle.kts` or provide the app's configured backend URL.

From the `mobile/` directory, with Android SDK and Java 17 available:

```powershell
.\gradlew.bat :app:assembleDebug
```

Install the resulting APK with Android Studio or:

```powershell
adb install app\build\outputs\apk\debug\app-debug.apk
```

The app requests camera, microphone, Bluetooth, and notification-related permissions as needed by the Android version and selected workflow.

## Testing and Checks

Python tests currently live under `backend/tests/`.

```powershell
python -m pytest backend/tests
```

A useful smoke check after starting either API is to open `/health` and `/docs`.

## Development Notes

- The database backend uses simple password comparison in its current development implementation; it is not production authentication.
- CORS is currently configured as `*` in both FastAPI applications. Restrict it before deployment.
- Hazard alert history is in memory and is limited to 500 entries. Persisted audit incidents use the separate audit database.
- Uploaded images and audio are stored under runtime `uploads/` directories and are served by the database backend at `/uploads`.
- AI output is safety guidance and does not replace a competent site supervisor, engineering assessment, or applicable regulations.
- The VLM, STT, FAISS, and optional YOLO components can fail independently during startup; inspect logs and `/health` before relying on detection results.
