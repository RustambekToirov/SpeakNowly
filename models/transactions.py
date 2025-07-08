from tortoise import fields
from .base import BaseModel
from enum import Enum

class TransactionType(str, Enum):
    """Enumeration for different types of token transactions."""
    TEST_READING = "READING"
    TEST_WRITING = "WRITING"
    TEST_LISTENING = "LISTENING"
    TEST_SPEAKING = "SPEAKING"
    DAILY_BONUS = "DAILY_BONUS"
    REFERRAL_BONUS = "REFERRAL_BONUS"
    CUSTOM_DEDUCTION = "CUSTOM_DEDUCTION"
    CUSTOM_ADDITION = "CUSTOM_ADDITION"
    REFUND = "REFUND"

class TokenTransaction(BaseModel):
    """Tortoise ORM model for storing token transactions."""
    user = fields.ForeignKeyField("models.User", related_name="token_transactions", description="User", index=True)
    transaction_type = fields.CharEnumField(TransactionType, description="Transaction Type", index=True)
    amount = fields.IntField(description="Amount")
    balance_after_transaction = fields.IntField(description="Balance After Transaction")
    description = fields.TextField(null=True, description="Description")

    class Meta:
        table = "token_transactions"
        verbose_name = "Token Transaction"
        verbose_name_plural = "Token Transactions"
        indexes = [("user_id",), ("transaction_type",)]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.transaction_type} ({self.amount})"