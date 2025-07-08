from tortoise.exceptions import DoesNotExist
from models import User
from models.tests import TestType

async def get_user_actual_test_price(user: User, test_type: str) -> float | None:
    """
    Gets actual test price based on user's tariff.
    """
    try:
        test = await TestType.get(type=test_type)
    except DoesNotExist:
        return None

    await user.fetch_related("tariff")

    if not user.tariff or user.tariff.is_default:
        return test.trial_price
    return test.price
