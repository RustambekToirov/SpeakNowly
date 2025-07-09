import httpx
import logging
from typing import Optional, Dict
from urllib.parse import quote
from decouple import config

logger = logging.getLogger("mirpay")

class MirPayService:
    """
    MirPay.uz API bilan ishlovchi xizmat:
    - Token olish
    - To‘lov yaratish (invoice)
    """
    def __init__(self):
        self.base_url = "https://mirpay.uz"
        self.kassa_id = config("MIRPAY_KASSA_ID")
        self.api_key = config("MIRPAY_API_KEY")
        self._client = httpx.AsyncClient(timeout=10)
        self._token: Optional[str] = None

    async def get_token(self) -> str:
        """Tokenni serverdan oladi va saqlaydi"""
        url = f"{self.base_url}/api/connect?kassaid={self.kassa_id}&api_key={self.api_key}"
        logger.info(f"🔐 Requesting token from: {url}")
        print(f"🔐 Requesting token from: {url}")

        response = await self._client.post(url)
        response.raise_for_status()

        data = response.json()
        self._token = data["token"]
        logger.info("✅ Token received")
        print(f"✅ Token: {self._token}")
        return self._token

    async def _get_auth_headers(self, force_refresh: bool = False) -> Dict[str, str]:
        """Tokenni tayyorlaydi, kerak bo‘lsa yangidan oladi"""
        if not self._token or force_refresh:
            await self.get_token()
        return {
            "Authorization": f"Bearer {self._token}"
        }

    async def create_invoice(self, summa: int, info_pay: str) -> Dict:
        """
        To‘lov yaratish: /api/create-pay
        :param summa: so‘mda (masalan 1000)
        :param info_pay: izoh (user ID yoki order haqida)
        :return: {'invoice_id', 'redirect_url', 'status', 'raw'}
        """
        # Har doim yangi token olish
        self._token = None
        headers = await self._get_auth_headers()

        encoded_info = quote(info_pay, safe='')
        url = f"{self.base_url}/api/create-pay?summa={summa}&info_pay={encoded_info}"
        logger.info(f"💳 Creating invoice: {url}")
        print(f"💳 Creating invoice: {url}")
        print(f"🧾 Headers: {headers}")

        try:
            response = await self._client.post(url, headers=headers)
            print(f"📨 Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Invoice created: {data}")
            print(f"📦 Invoice response JSON: {data}")
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
            print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("❌ Unexpected error during invoice creation")
            print(f"❌ Unexpected error: {str(e)}")
            raise

        return {
            "invoice_id": data.get("id"),
            "redirect_url": data.get("payinfo", {}).get("redicet_url", ""),
            "status": data.get("payinfo", {}).get("status", ""),
            "raw": data
        }

    async def close(self):
        await self._client.aclose()


# Global singleton
mirpay = MirPayService()
