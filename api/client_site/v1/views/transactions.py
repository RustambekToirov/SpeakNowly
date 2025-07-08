from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from ..serializers.transactions import (
    TokenTransactionSerializer,
    TokenTransactionCreateSerializer,
    TokenTransactionListSerializer,
    TokenTransactionDetailSerializer,
)
from ..serializers.payments import PaymentCreateSerializer
from models import TokenTransaction, TransactionType, User
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()


@router.get("/", response_model=List[TokenTransactionListSerializer])
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    transaction_type: Optional[TransactionType] = Query(None),
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """List all token transactions for current user."""
    offset = (page - 1) * page_size
    query = TokenTransaction.filter(user_id=user.id)
    if transaction_type:
        query = query.filter(transaction_type=transaction_type)
    transactions = await query.offset(offset).limit(page_size).all()
    if not transactions:
        raise HTTPException(status_code=404, detail=t.get("no_transactions", "No transactions found for the user"))
    return transactions


@router.post("/", response_model=TokenTransactionSerializer, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TokenTransactionCreateSerializer,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """Create a new token transaction for current user."""
    if transaction_data.user_id != user.id:
        raise HTTPException(status_code=403, detail=t.get("permission_denied", "You cannot create transactions for another user"))
    last_transaction = await TokenTransaction.filter(user_id=user.id).order_by("-created_at").first()
    current_balance = last_transaction.balance_after_transaction if last_transaction else 0
    new_balance = current_balance + transaction_data.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail=t.get("insufficient_balance", "Insufficient balance for this transaction"))
    transaction = await TokenTransaction.create(
        user=user,
        transaction_type=transaction_data.transaction_type,
        amount=transaction_data.amount,
        balance_after_transaction=new_balance,
        description=transaction_data.description,
    )
    return transaction


@router.get("/{transaction_id}/", response_model=TokenTransactionDetailSerializer)
async def get_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """Retrieve a specific token transaction by ID."""
    try:
        transaction = await TokenTransaction.get(id=transaction_id, user_id=user.id).select_related("user")
        return {
            "user": {
                "id": transaction.user.id,
                "email": transaction.user.email,
                "first_name": transaction.user.first_name,
                "last_name": transaction.user.last_name,
            },
            "transaction_type": transaction.transaction_type,
            "amount": transaction.amount,
            "balance_after_transaction": transaction.balance_after_transaction,
            "description": transaction.description,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t.get("transaction_not_found", "Transaction not found"))


@router.delete("/{transaction_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """Delete a specific token transaction by ID."""
    deleted_count = await TokenTransaction.filter(id=transaction_id, user_id=user.id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=t.get("transaction_not_found", "Transaction not found"))
    return {"message": t.get("transaction_deleted", "Transaction deleted successfully")}


@router.post("/checkout/", status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: PaymentCreateSerializer):
    async with in_transaction():
        # ...вся логика создания платежа и invoice...
        # если будет raise — всё откатится
        pass