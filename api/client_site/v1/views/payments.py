from fastapi import APIRouter, HTTPException, status, Depends, Request, Form
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from tortoise.exceptions import DoesNotExist

from ..serializers.payments import PaymentCreateSerializer, PaymentSerializer
from services.payments.mirpay_service import mirpay
from models import Payment, Tariff, TokenTransaction, TransactionType, Message
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()


@router.post("/checkout/", response_model=PaymentSerializer, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: PaymentCreateSerializer,
    user=Depends(get_current_user),
    t=Depends(get_translation)
):
    """
    1. Tariffni tekshir
    2. Foydalanuvchida mavjud active to‘lov borligini tekshir
    3. Pending bo‘lgan to‘lovni qayta ishlat yoki yarat
    4. MirPay orqali invoice yarat
    5. payment_url va invoice_id ni saqlab yubor
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
        inv = await mirpay.create_invoice(
            summa=payment.amount,
            info_pay=f"User ID: {user.id} - Payment ID: {payment.uuid}"
        )
    except Exception as e:
        msg = t.get("mirpay_error", "Payment service error: {error}").format(error=str(e))
        raise HTTPException(502, msg)

    await payment.update_from_dict({
        "mirpay_invoice_id": inv["invoice_id"],
        "mirpay_status": inv["status"],
        "mirpay_response": inv["raw"]
    }).save()

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=user.id,
        tariff_id=tariff.id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=inv["invoice_id"],
        atmos_status=inv["status"],
        payment_url=inv["redirect_url"]
    )


@router.post("/callback/", status_code=200)
async def callback(
    payid: str = Form(...),
    summa: str = Form(...),
    status: str = Form(...),
    comment: str = Form(...),
    chek: str = Form(...),
    fiskal: str = Form(...),
    sana: str = Form(...),
    t=Depends(get_translation)
):
    """
    MirPay dan keladigan callbackni qabul qiladi.
    Agar status = success bo‘lsa, paymentni "paid" qiladi va token beradi.
    """
    if status.lower() != "success":
        raise HTTPException(400, t.get("invalid_callback", "Payment not successful"))

    try:
        payment = await Payment.get(mirpay_invoice_id=payid).select_related("tariff", "user")
    except DoesNotExist:
        raise HTTPException(404, t.get("payment_not_found", "Payment not found"))

    if payment.status == "paid":
        return {"status": "ok"}

    payment.status = "paid"
    await payment.save()

    tokens = payment.tariff.tokens
    last = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
    bal = last.balance_after_transaction if last else 0

    await TokenTransaction.create(
        user=payment.user,
        transaction_type=TransactionType.CUSTOM_ADDITION,
        amount=tokens,
        balance_after_transaction=bal + tokens,
        description=t.get("tokens_for_tariff", "Tokens for {tariff_name}").format(
            tariff_name=payment.tariff.name
        )
    )

    await Message.create(
        user=payment.user,
        type="site",
        title=f"To‘lov qabul qilindi. Sana: {payment.start_date:%Y-%m-%d}",
        description="MirPay orqali to‘lov muvaffaqiyatli amalga oshirildi.",
        content=(
            f"## ✅ Obuna tasdiqlandi\n\n"
            f"**Tarif:** {payment.tariff.name}\n"
            f"**Narx:** {payment.tariff.price} STARS\n"
            f"**Muddat:** {payment.tariff.duration} kun\n\n"
            f"**Boshlanish:** {payment.start_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"**Tugash:** {payment.end_date.strftime('%Y-%m-%d %H:%M')}"
        )
    )

    return {"status": "ok"}
