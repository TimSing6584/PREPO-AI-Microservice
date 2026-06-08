# Speech Assessment Microservice

A FastAPI microservice that converts speech to text and assesses the response using an LLM.

---

## Prerequisites

- Python 3.11+
- Git

---

## Getting Started

### 1. Clone the repo

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Create a virtual environment

**Mac/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

> You should see `(.venv)` in your terminal. Run `deactivate` to exit it.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Then open `.env` and fill in your values. There are two ways:

---

## Secret Management

### Infisical

<!-- Set only these 3 vars in your `.env`:

```env
INFISICAL_SERVICE_TOKEN=st.your_token_here
INFISICAL_PROJECT_ID=your_project_id
INFISICAL_ENV=dev
```

The app will automatically fetch all other secrets (API keys, URLs, etc.) from Infisical on startup.

To get a service token: Infisical dashboard → your project → **Access Control** → **Service Tokens** → Create.

To get a project id: Infisical dashboard → your project → **Settings** → Copy Project ID. -->

We don't need to manually put environment variables into .env file because if you already installed Infisical locally you just run

```bash
infisical login
```

then run this command to select the right project

```bash
infisical init
```

Later when the server can actually run, we can use chained command supported by Infisical like : infisical run --env=dev --path=/ uvicorn main.py .... (when we use infisical run ..., Infisical automatically injects environment variables into our code)

Additionally, here is the command to write all environment variables to .env:

```bash
infisical export --env=dev --path=/ --format=dotenv --output-file=.env
```


---

## Running the App

```bash
uvicorn src.main:app --reload
```

API is now live at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

---

## Project Structure

```
src/
├── speech_to_text/
│   ├── router.py          # POST /transcribe
│   ├── schemas.py         # AudioInput, TranscriptOutput
│   ├── service.py         # Calls Deepgram/Whisper API
│   ├── config.py          # DEEPGRAM_API_KEY, WHISPER_URL, etc.
│   ├── exceptions.py      # TranscriptionError
│   └── utils.py           # Audio format validation, chunking
│
├── assessment/
│   ├── router.py          # POST /assess
│   ├── schemas.py         # AssessmentInput, AssessmentOutput
│   ├── service.py         # Calls LLM API
│   ├── config.py          # OLLAMA_URL (if used), model name, etc.
│   ├── exceptions.py      # AssessmentError
│   └── utils.py           # Prompt building helpers
│
├── pipeline/
│   ├── router.py          # POST /pipeline/speech-assess  ← main entry
│   ├── schemas.py         # PipelineInput, PipelineOutput
│   └── service.py         # Orchestrates STT → LLM sequentially
│
├── config.py              # Global settings
├── exceptions.py          # Global handlers
├── database.py            # (optional, if you log results)
└── main.py
```

---

## The Mental Model

```
POST /pipeline/speech-assess
        │
        ▼
 pipeline/service.py          ← orchestrates, owns the sequence
        │
        ├──► stt/service.py   ← knows only about audio → text
        │         │
        │    TranscriptOutput
        │
        └──► assessment/service.py  ← knows only about text → score
                  │
             AssessmentOutput
```

Each domain service is **unaware of the other** — `pipeline/service.py` is the only place that knows the order. This makes it easy to swap Deepgram → Whisper or Ollama → GPT-4 by only touching one domain's config, and the pipeline stays untouched.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transcribe` | Convert audio file to text |
| POST | `/assessment` | Assess a transcript against a model answer |
| POST | `/pipeline/speech-assess` | Run full STT → assessment pipeline |

---

## Deployment (Render)

1. Push your code to GitHub (`.env` is gitignored — never committed)
2. Create a new **Web Service** on Render, connect your repo


3. Set start command:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

All other secrets are pulled from Infisical automatically at boot.

---

## Common Issues

**`ModuleNotFoundError: No module named 'src'`**
Run the app from the project root, not inside the `src/` folder:
```bash
# correct
uvicorn src.main:app --reload

# wrong
cd src && uvicorn main:app --reload
```

**`.venv` not activating on Windows**
```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Then retry `.venv\Scripts\activate`.

**Secrets not loading from Infisical**
Make sure `INFISICAL_PROJECT_ID` is set — the app silently falls back to `.env` if Infisical credentials are missing.FastAPI structure domain-based (every folder for 1 domain, and they only connect at pipeline/)
