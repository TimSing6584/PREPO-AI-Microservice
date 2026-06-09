from pydantic_settings import BaseSettings

class STTConfig(BaseSettings):
    DEEPGRAM_API_KEY: str                                          # required — no default
    DEEPGRAM_URL: str = "https://api.deepgram.com/v1/listen"      # safe to keep as default

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

stt_config = STTConfig()
