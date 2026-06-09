from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .exceptions import AppException, app_exception_handler
from .speech_to_text.router import router as stt_router
from .assessment.router import router as assessment_router
from .pipeline.router import router as pipeline_router

app = FastAPI(title="Speech Assessment Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend origin
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(stt_router)
app.include_router(assessment_router)
app.include_router(pipeline_router)
