import asyncio
from datetime import datetime, timezone
from arq.connections import RedisSettings

from services.analyses import (
    ListeningAnalyseService,
    ReadingAnalyseService,
    SpeakingAnalyseService,
    WritingAnalyseService,
)
from services.users.email_service import EmailService
from models import User, UserActivityLog, Payment, Tariff, TokenTransaction, Message

from tortoise import Tortoise


# === Database Initialization ===

async def ensure_tortoise():
    if not Tortoise._inited:
        from config import DATABASE_URL
        await Tortoise.init(
            db_url=DATABASE_URL,
            modules={
                "models": [
                    "models.users.users",
                    "models.users.verification_codes",
                    "models.tests",
                    "models.analyses",
                    "models.payments",
                    "models.tariffs",
                    "models.transactions",
                    "models.notifications",
                    "models.comments",
                    "aerich.models"
                ]
            }
        )


# === Analysis Tasks ===

async def analyse_listening(ctx, session_id: int):
    await ensure_tortoise()
    await ListeningAnalyseService.analyse(session_id)


async def analyse_reading(ctx, reading_id: int, user_id: int):
    await ensure_tortoise()
    await ReadingAnalyseService.analyse(reading_id, user_id)


async def analyse_speaking(ctx, test_id: int, lang_code: str, t: dict):
    await ensure_tortoise()
    await SpeakingAnalyseService.analyse(test_id, lang_code=lang_code, t=t)


async def analyse_writing(ctx, test_id: int, lang_code: str, t: dict):
    await ensure_tortoise()
    await WritingAnalyseService.analyse(test_id, lang_code=lang_code, t=t)


# === Email Tasks ===

async def send_email(ctx, subject: str, recipients: list[str], body: str = None, html_body: str = None):
    await ensure_tortoise()
    await EmailService.send_email(subject, recipients, body, html_body)


# === User Activity Tasks ===

async def log_user_activity(ctx, user_id: int, action: str):
    await ensure_tortoise()
    user = await User.get_or_none(id=user_id)
    if user:
        await UserActivityLog.create(user=user, action=action)


# === Tariff Management Tasks ===

async def check_expired_tariffs(ctx):
    await ensure_tortoise()
    now = datetime.now(timezone.utc)
    default = await Tariff.filter(is_default=True).first()
    users = await User.all().select_related("tariff")

    for user in users:
        payment = await Payment.filter(user_id=user.id).order_by("-end_date").first()
        if not payment or payment.end_date >= now:
            continue

        user_tariff = await Tariff.get(id=user.tariff_id)
        if user_tariff.is_default:
            continue

        user.tariff_id = default.id
        await user.save(update_fields=["tariff_id"])
        await Message.create(
            user_id=user.id,
            title="📅 Tariff Expired",
            type="site",
            description="Your subscription has expired.",
            content=(
                f"Your subscription to **{user_tariff.name}** expired on "
                f"{payment.end_date:%Y-%m-%d %H:%M}.\n\n"
                f"You have been switched to **{default.name}**."
            ),
        )


async def give_daily_tariff_bonus(ctx):
    await ensure_tortoise()
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    users = await User.filter(tariff_id__not=None).select_related("tariff")

    for user in users:
        tariff = await Tariff.get_or_none(id=user.tariff_id)
        if not tariff or tariff.is_default:
            continue

        already_given = await TokenTransaction.filter(
            user_id=user.id,
            transaction_type=TokenTransaction.DAILY_BONUS,
            created_at__gte=today
        ).exists()

        if already_given:
            continue

        user.tokens = tariff.tokens
        await user.save(update_fields=["tokens"])
        await TokenTransaction.create(
            user_id=user.id,
            transaction_type=TokenTransaction.DAILY_BONUS,
            amount=tariff.tokens,
            balance_after_transaction=user.tokens,
            description=f"Daily bonus for {tariff.name} on {now:%Y-%m-%d}"
        )
        await Message.create(
            user_id=user.id,
            title="🎁 Daily Bonus Received",
            type="site",
            description="Your daily token bonus has been credited.",
            content=f"You received **{tariff.tokens} TOKENS** for **{tariff.name}** on {now:%Y-%m-%d}."
        )


# === ARQ Worker Configuration ===

class WorkerSettings:
    redis_settings = RedisSettings(host="localhost", port=6379)
    functions = [
        analyse_listening,
        analyse_reading,
        analyse_speaking,
        analyse_writing,
        send_email,
        log_user_activity,
        check_expired_tariffs,
        give_daily_tariff_bonus,
    ]

    async def startup(self, ctx):
        from redis.asyncio import Redis
        from config import DATABASE_URL, REDIS_URL

        try:
            # === Redis initialization ===
            ctx["redis"] = Redis.from_url(REDIS_URL, decode_responses=True)
            await ctx["redis"].ping()
            print("✅ Redis connected")

            # === Tortoise initialization ===
            await Tortoise.init(
                db_url=DATABASE_URL,
                modules={
                    "models": [
                        "models.users.users",
                        "models.users.verification_codes",
                        "models.tests.listening",
                        "models.tests.reading",
                        "models.tests.speaking",
                        "models.tests.writing",
                        "models.tests.test_type",
                        "models.analyses",
                        "models.payments",
                        "models.tariffs",
                        "models.transactions",
                        "models.notifications",
                        "models.comments",
                        "aerich.models"
                    ]
                }
            )
            print("✅ Tortoise ORM initialized")

        except Exception as e:
            print(f"❌ Startup error: {e}")
            raise

    async def shutdown(self, ctx):
        try:
            await ctx["redis"].close()
            await Tortoise.close_connections()
            print("🛑 Connections closed")
        except Exception as e:
            print(f"❌ Shutdown error: {e}")
