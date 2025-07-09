from pydantic import BaseModel
from typing import Optional, List

class FeatureInfo(BaseModel):
    """Feature info."""
    id: int
    name: str
    description: Optional[str]

class FeatureItemInfo(BaseModel):
    """Tariff feature item."""
    id: int
    tariff: int
    feature: FeatureInfo
    is_included: bool

class TariffInfo(BaseModel):
    """Tariff info."""
    id: int
    name: str
    old_price: Optional[int]  # ⬅️ float emas!
    price: int                # ⬅️ float emas!
    description: str
    tokens: int
    duration: int
    features: List[FeatureItemInfo]
    is_default: bool
    redirect_url: Optional[str]


class PlanInfo(BaseModel):
    """Plan (category) info."""
    id: int
    name: str
    sale: float
    tariffs: List[TariffInfo]