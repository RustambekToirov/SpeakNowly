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
        logger.info(f"🔐 [MirPay] Token so‘rovi: {url}")
        try:
            response = await self._client.post(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ [MirPay] Token olishda xatolik: {e} | Javob: {response.text}")
            raise

        data = response.json()
        self._token = data["token"]
        logger.info("✅ [MirPay] Token olindi")
        return self._token

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Tokenni tayyorlaydi, kerak bo‘lsa yangidan oladi"""
        if not self._token:
            await self.get_token()
        return {
            "Authorization": f"Bearer {self._token}"
        }

    async def create_invoice(self, summa: int, info_pay: str) -> Dict:
        headers = await self._get_auth_headers()
        encoded_info = quote(info_pay)
        url = f"{self.base_url}/api/create-pay?summa={summa}&info_pay={encoded_info}"
        logger.info(f"💳 Creating invoice: {url}")

        response = await self._client.post(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✅ Invoice created: {data}")

        # 👇 YANGILIK: butun javobni raw qilib saqlaymiz
        payinfo = data.get("payinfo", {})

        return {
            "invoice_id": payinfo.get("id", ""),  # Agar 'id' yo‘q bo‘lsa, bo‘sh string bo‘ladi
            "redirect_url": payinfo.get("redicet_url", ""),
            "status": payinfo.get("status", ""),
            "raw": data
        }

    async def close(self):
        await self._client.aclose()


# Singleton instance
mirpay = MirPayService()
