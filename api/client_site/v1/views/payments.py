from fastapi import APIRouter, HTTPException, status, Depends, Request
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from tortoise.exceptions import DoesNotExist
from starlette.responses import JSONResponse

from ..serializers.payments import PaymentCreateSerializer, PaymentSerializer
from services.payments.atmos_service import atm
from models import Payment, Tariff, TokenTransaction, TransactionType, Message
from utils.auth import get_current_user
from utils.i18n import get_translation

FRONT_NOTIFY_BASE = "https://speaknowly.com/dashboard/notification"

router = APIRouter()

@router.post("/checkout/", response_model=PaymentSerializer, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: PaymentCreateSerializer,
    user=Depends(get_current_user),
    t=Depends(get_translation)
):
    """
    1) Load tariff
    2) Prevent duplicate active subscription
    3) Reuse or create a pending Payment
    4) Call Atmos to create invoice + payment_url
    5) Save Atmos info and return to client
    """
    try:
        tariff = await Tariff.get(id=data.tariff_id)
    except DoesNotExist:
        raise HTTPException(404, t.get("tariff_not_found", "Tariff not found"))

    now = datetime.now(timezone.utc)
    already = await Payment.filter(
        user_id=user.id,
        tariff_id=tariff.id,
        end_date__gte=now,
        status="paid"
    ).first()
    if already:
        raise HTTPException(400, t.get("payment_exists", "Active payment exists"))

    payment = await Payment.filter(
        user_id=user.id, tariff_id=tariff.id, status="pending"
    ).first()
    if not payment:
        start = now
        end = now + timedelta(days=tariff.duration)
        payment = await Payment.create(
            uuid=uuid4(),
            user=user,
            tariff=tariff,
            amount=tariff.price,
            start_date=start,
            end_date=end,
            status="pending"
        )

    try:
        inv = await atm.create_invoice(
            request_id=str(payment.uuid),
            amount_tiyin=payment.amount * 100
        )
    except Exception as e:
        msg = t.get("atm_error", "Payment service error: {error}").format(error=str(e))
        raise HTTPException(502, msg)

    await payment.update_from_dict({
        "atmos_invoice_id": str(inv["transaction_id"]),
        "atmos_status": inv["result"].get("code"),
        "atmos_response": inv["store_transaction"]
    }).save()

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=user.id,
        tariff_id=tariff.id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=str(inv["transaction_id"]),
        atmos_status=inv["result"].get("code"),
        payment_url=inv["payment_url"]
    )


@router.post("/callback/", status_code=200)
async def callback(req: Request, t=Depends(get_translation)):
    """
    Atmos webhook:
    - ensure result.code == "OK"
    - mark Payment as paid
    - credit tokens
    - create a Message
    - return front redirect_url
    """

    allowed_ips = {"1.2.3.4", "5.6.7.8"}  # Replace with actual Atmos IPs
    client_ip = req.client.host
    if client_ip not in allowed_ips:
        raise HTTPException(403, t.get("forbidden", "Forbidden"))

    try:
        payload = await req.json()
    except Exception:
        raise HTTPException(400, t.get("invalid_callback", "Invalid callback (no JSON)"))

    txn = payload.get("transaction_id")
    code = payload.get("result", {}).get("code")
    if not txn or code != "OK":
        raise HTTPException(400, t.get("invalid_callback", "Invalid callback"))

    try:
        payment = await Payment.get(atmos_invoice_id=str(txn)).select_related("tariff", "user")
    except DoesNotExist:
        raise HTTPException(404, t.get("payment_not_found", "Payment not found"))

    if payment.status == "paid":
        return {"status": "ok"}

    payment.status = "paid"
    await payment.save()

    # award tokens
    tokens = payment.tariff.tokens
    last = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
    bal = last.balance_after_transaction if last else 0
    await TokenTransaction.create(
        user=payment.user,
        transaction_type=TransactionType.CUSTOM_ADDITION,
        amount=tokens,
        balance_after_transaction=bal + tokens,
        description=t.get("tokens_for_tariff", "Tokens for {tariff_name}").format(tariff_name=payment.tariff.name)
    )

    # create a notification message
    start_date = payment.start_date
    end_date = payment.end_date
    tariff = payment.tariff

    await Message.create(
        user=payment.user,
        type="site",
        title=f"Payment created successfully. Date {start_date:%Y-%m-%d}",
        description="Payment created successfully. Congratulations!",
        content=(
            f"## 🎉 Subscription Activated Successfully!\n\n"
            f"**Tariff Name:** {tariff.name}  \n"
            f"**Price:** {tariff.price} STARS  \n"
            f"**Duration:** {tariff.duration} days  \n\n"
            f"---\n\n"
            f"**Start Date:** {start_date.strftime('%Y-%m-%d %H:%M')}  \n"
            f"**End Date:** {end_date.strftime('%Y-%m-%d %H:%M')}"
        )
    )

    return {"status": "ok"}
