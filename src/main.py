from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .exceptions import AppException, app_exception_handler
from .speech_to_text.router import router as stt_router
from .assessment.router import router as assessment_router
from .pipeline.router import router as pipeline_router
from .config import settings
import logging
import sentry_sdk

logging.basicConfig(level=logging.INFO) # Configure logging at the INFO level

sentry_sdk.init(
    dsn=settings.SENTRY_DSN
)

app = FastAPI(title="Speech Assessment Microservice")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # your frontend origin
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_exception_handler(AppException, app_exception_handler)


app.include_router(stt_router)
app.include_router(assessment_router)
app.include_router(pipeline_router)


from fastapi import Depends
from .utils.security import verify_jwt


@app.get("/health", tags=["health"], dependencies=[Depends(verify_jwt)])
async def health() -> dict:
    """Authenticated warm-up/health probe.

    The Next.js frontend pings this (with a service JWT) when a user shows
    intent to record, so this serverless instance spins up on Render before
    audio is submitted. JWT-protected like every other route so it can't be
    abused anonymously to keep the box warm; does no work otherwise — it only
    needs to land a request that wakes the instance.
    """
    return {"status": "ok"}
