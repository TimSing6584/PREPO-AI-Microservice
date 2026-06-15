import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def verify_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SPEECH_ASSESS_SERVICE_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token") from exc

    request.state.user_id = payload.get("sub")
    return payload