from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SPEECH_ASSESS_SERVICE_JWT_SECRET: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()