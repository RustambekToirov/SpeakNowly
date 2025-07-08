from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError, ExpiredSignatureError

from utils.auth import create_access_token, create_refresh_token
from config import SECRET_KEY, ALGORITHM

router = APIRouter()

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh/")
async def refresh_access_token(payload: TokenRefreshRequest):
    """
    Refresh access and refresh tokens using a valid refresh token.

    Steps:
    1. Decode and validate refresh token.
    2. Check token type.
    3. Generate new tokens.
    4. Return new tokens.
    """
    try:
        payload_data = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload_data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload_data.get("sub")
        email = payload_data.get("email")
        access_token = await create_access_token(subject=user_id, email=email)
        refresh_token = await create_refresh_token(subject=user_id, email=email)
        return {"access_token": access_token, "refresh_token": refresh_token}
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
