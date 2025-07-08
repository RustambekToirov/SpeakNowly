import base64
import time
import httpx
from decouple import config
from typing import Any, Dict
from pydantic import BaseModel

class AtmosAuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AtmosCreateResponse(BaseModel):
    """Matches Atmos /merchant/pay/create response."""
    result: Dict[str, Any]
    transaction_id: int
    store_transaction: Dict[str, Any]

class AtmosService:
    """
    Atmos API client:
    - Fetch OAuth token from /token
    - Create draft transaction via /merchant/pay/create
    - Build payment page URL on checkout.pays.uz
    """
    def __init__(self):
        self.base = "https://partner.atmos.uz"
        self.api = f"{self.base}/merchant"
        self.token_url = f"{self.base}/token"

        self.store_id = config("ATMOS_MERCHANT_ID")
        self.key = config("ATMOS_CONSUMER_KEY")
        self.secret = config("ATMOS_CONSUMER_SECRET")

        self._token: str | None = None
        self._expiry: float = 0.0
        self._client = httpx.AsyncClient(timeout=10)

    async def _ensure_token(self):
        """Obtain and cache a valid OAuth2 bearer token."""
        now = time.time()
        if self._token and now < self._expiry:
            return

        creds = f"{self.key}:{self.secret}".encode()
        basic = base64.b64encode(creds).decode()
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        r = await self._client.post(self.token_url, data=data, headers=headers)
        r.raise_for_status()
        auth = AtmosAuthResponse(**r.json())

        self._token = auth.access_token
        self._expiry = now + auth.expires_in - 5

    async def create_invoice(
        self,
        request_id: str,
        amount_tiyin: int,
        lang: str = "ru",
        notify_id: int | None = None
    ) -> Dict[str, Any]:
        """
        1) Create draft via POST /merchant/pay/create
        2) Return dict with:
           - result
           - transaction_id
           - store_transaction
           - payment_url (checkout.pays.uz link)
        """
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        payload = {
            "amount": amount_tiyin,
            "account": request_id,
            "store_id": self.store_id,
            "lang": lang,
        }

        # create a draft transaction
        r = await self._client.post(f"{self.api}/pay/create", json=payload, headers=headers)
        r.raise_for_status()
        data = AtmosCreateResponse(**r.json())

        tx = data.transaction_id

        redirect_link = "https://speaknowly.com/dashboard/notification"

        # build the hosted payment page URL
        payment_url = (
            f"https://checkout.pays.uz/invoice/get?"
            f"storeId={self.store_id}"
            f"&transactionId={tx}"
            f"&redirectLink={redirect_link}"
        )

        return {
            "result": data.result,
            "transaction_id": tx,
            "store_transaction": data.store_transaction,
            "payment_url": payment_url,
        }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

# Singleton
atm = AtmosService()
