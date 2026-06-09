from src.exceptions import AppException

class AssessmentError(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=502, detail=detail)