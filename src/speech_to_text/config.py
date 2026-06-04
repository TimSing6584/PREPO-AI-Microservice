from pydantic_settings import BaseSettings

class STTConfig(BaseSettings):
    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_URL: str = "https://api.deepgram.com/v1/listen"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

stt_config = STTConfig()
