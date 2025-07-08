import httpx
import jwt
from jwcrypto import jwk
from fastapi import HTTPException

JWK_URL = "https://appleid.apple.com/auth/keys"
TOKEN_AUDIENCE = "https://appleid.apple.com"

async def get_apple_jwk(kid: str) -> dict:
    """
    Fetches Apple's public JWK for given key ID.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWK_URL, timeout=5)
            resp.raise_for_status()
            jwks = resp.json().get("keys", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch JWKs: {e}")

    for key in jwks:
        if key.get("kid") == kid:
            return key
    raise HTTPException(status_code=400, detail="JWK not found for given kid")

async def decode_apple_id_token(id_token: str, client_id: str) -> dict:
    """
    Decodes and validates Apple ID token using JWKS.
    """
    if not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token parameter")

    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=400, detail="Missing kid in token header")

        jwk_data = await get_apple_jwk(kid)
        key = jwk.JWK(**jwk_data)
        public_key = key.export_to_pem().decode("utf-8")

        decoded = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=TOKEN_AUDIENCE
        )
        return decoded

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Apple token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Apple token: {e}")