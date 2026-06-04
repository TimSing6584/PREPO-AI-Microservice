# assessment/config.py
class AssessmentConfig(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"          # ← add this