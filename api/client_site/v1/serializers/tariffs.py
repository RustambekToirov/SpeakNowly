from pydantic import BaseModel
from typing import Optional, List


class FeatureInfo(BaseModel):
    """Yagona feature obyekti."""
    id: int
    name: str
    description: Optional[str]


class FeatureItemInfo(BaseModel):
    """Tariffga tegishli feature holati."""
    id: int
    tariff: int
    feature: FeatureInfo
    is_included: bool


class TariffInfo(BaseModel):
    """Alohida tarif (plan ichidagi variant)."""
    id: int
    name: str
    old_price: Optional[float]  # float bo'lishi kerak, lekin optional
    price: int
    description: str
    tokens: int
    duration: int
    features: List[FeatureItemInfo]
    is_default: bool
    redirect_url: Optional[str]


class PlanInfo(BaseModel):
    """Asosiy plan (kategoriya), ichida bir nechta tariff bor."""
    id: int
    name: str
    sale: int
    tariffs: List[TariffInfo]
