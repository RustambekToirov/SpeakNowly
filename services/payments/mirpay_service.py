import httpx
from typing import Optional, Dict
from decouple import config
from urllib.parse import quote

class MirPayService:
    """
    MirPay.uz API bilan ishlovchi xizmat:
    - Token olish
    - To‘lov yaratish
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
        response = await self._client.post(url)
        response.raise_for_status()

        data = response.json()
        self._token = data["token"]
        return self._token

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Tokenni tayyorlaydi, kerak bo‘lsa yangidan oladi"""
        if not self._token:
            await self.get_token()
        return {
            "Authorization": f"Bearer {self._token}"
        }

    async def create_invoice(self, summa: int, info_pay: str) -> Dict:
        """
        To‘lov yaratish: /api/create-pay
        :param summa: so‘mda (int) masalan 1000
        :param info_pay: to‘lov izohi (foydalanuvchi yoki buyurtma haqida)
        :return: {'invoice_id', 'redirect_url', 'status', 'raw'}
        """
        headers = await self._get_auth_headers()
        encoded_info = quote(info_pay)
        url = f"{self.base_url}/api/create-pay?summa={summa}&info_pay={encoded_info}"

        response = await self._client.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "invoice_id": data.get("id"),
            "redirect_url": data.get("payinfo", {}).get("redirect_url"),
            "status": data.get("payinfo", {}).get("status"),
            "raw": data
        }

    async def close(self):
        await self._client.aclose()


# Singleton
mirpay = MirPayService()
