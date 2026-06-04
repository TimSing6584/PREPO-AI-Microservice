# prepo-AI-microservice
FastAPI structure domain-based (every folder for 1 domain, and they only connect at pipeline/)

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