from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models import TransactionType

class TokenTransactionSerializer(BaseModel):
    user_id: int
    transaction_type: TransactionType
    amount: int
    balance_after_transaction: int
    description: Optional[str]

class TokenTransactionCreateSerializer(BaseModel):
    user_id: int = Field(..., description="User ID")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    amount: int = Field(..., description="Amount", ge=1)
    description: Optional[str] = None

class TokenTransactionListSerializer(BaseModel):
    user_id: int
    transaction_type: TransactionType
    amount: int
    balance_after_transaction: int
    created_at: datetime

class TokenTransactionDetailSerializer(BaseModel):
    user: dict
    transaction_type: TransactionType
    amount: int
    balance_after_transaction: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime