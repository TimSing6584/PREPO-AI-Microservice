from ..exceptions import AppException

class TranscriptionError(AppException):
    def __init__(self, detail: str = "Transcription failed"):
        super().__init__(status_code=502, detail=detail)
