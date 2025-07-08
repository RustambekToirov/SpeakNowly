from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from models import PaymentStatus

class PaymentCreateSerializer(BaseModel):
    """Payload for creating a checkout session."""
    tariff_id: int = Field(..., description="ID of the tariff to purchase")

class PaymentSerializer(BaseModel):
    """Response model for a payment."""
    uuid: UUID4 = Field(..., description="Internal payment UUID")
    user_id: int = Field(..., description="User ID")
    tariff_id: int = Field(..., description="Tariff ID")
    amount: int = Field(..., description="Amount in local currency")
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: datetime = Field(..., description="Subscription end date")
    status: PaymentStatus = Field(..., description="Payment status")
    atmos_invoice_id: Optional[str] = Field(None, description="Atmos transaction ID")
    atmos_status: Optional[str] = Field(None, description="Atmos result code")
    payment_url: Optional[str] = Field(None, description="URL to payment page")
