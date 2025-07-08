from fastapi import HTTPException, Request, status
from utils.get_actual_price import get_user_actual_test_price
from models.transactions import TokenTransaction, TransactionType
from tortoise.transactions import in_transaction

async def check_user_tokens(
    user,
    test_type: TransactionType,
    request: Request,
    t: dict
) -> bool:
    """
    Validates and deducts tokens for test operations.
    """
    price = await get_user_actual_test_price(user, test_type.value.lower())
    if price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t.get("test_type_not_found", "Test type not found")
        )

    if user.tokens < price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=t.get("not_enough_tokens", "Not enough tokens")
        )

    async with in_transaction():
        user.tokens -= price
        await user.save(update_fields=["tokens"])
        await TokenTransaction.create(
            user=user,
            transaction_type=test_type,
            amount=-price,
            balance_after_transaction=user.tokens,
            description=f"Test {test_type.value} started"
        )

    return True