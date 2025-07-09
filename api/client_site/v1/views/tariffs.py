from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

from ..serializers.tariffs import PlanInfo, TariffInfo, FeatureItemInfo, FeatureInfo
from models import TariffCategory
from services.cache_service import cache
from utils.i18n import get_translation

router = APIRouter()

def _translate(obj, field: str, lang: str) -> str:
    """Ma'lumotni tarjima qiladi yoki default qiymatni qaytaradi."""
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, field, "") or ""

@router.get("/", response_model=List[PlanInfo])
async def list_plans(
    request: Request,
    t: dict = Depends(get_translation),
):
    """Asosiy sahifa uchun barcha tarif rejalari va xususiyatlarini qaytarish."""
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()

    if lang not in {"en", "ru", "uz"}:
        raise HTTPException(status_code=400, detail=t.get("invalid_language", "Unsupported language"))

    cache_key = f"plans_{lang}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    categories = await TariffCategory.filter(is_active=True).prefetch_related(
        "tariffs__tariff_features__feature"
    )

    result: List[PlanInfo] = []
    for category in categories:
        category_name = _translate(category, "name", lang)
        tariffs_list: List[TariffInfo] = []

        for tariff in category.tariffs:
            if not tariff.is_active:
                continue

            t_name = _translate(tariff, "name", lang)
            t_desc = _translate(tariff, "description", lang)
            features_list: List[FeatureItemInfo] = []

            for tf in tariff.tariff_features:
                feat = tf.feature
                if not feat:
                    continue
                f_name = _translate(feat, "name", lang)
                f_desc = _translate(feat, "description", lang)
                feature_info = FeatureInfo(
                    id=feat.id,
                    name=f_name,
                    description=f_desc
                )
                feat_item = FeatureItemInfo(
                    id=tf.id,
                    tariff=tf.tariff_id,
                    feature=feature_info,
                    is_included=tf.is_included
                )
                features_list.append(feat_item)

            tariff_info = TariffInfo(
                id=tariff.id,
                name=t_name,
                price=tariff.price,
                old_price=tariff.old_price,
                description=t_desc,
                tokens=int(tariff.tokens),
                duration=int(tariff.duration),
                redirect_url=None,
                is_default=bool(tariff.is_default),
                features=features_list
            )
            tariffs_list.append(tariff_info)

        # ❗️Agar bu planda faol tariflar yo'q bo‘lsa, o'tkazib yuboramiz
        if not tariffs_list:
            continue

        plan_info = PlanInfo(
            id=category.id,
            name=category_name,
            sale=int(category.sale),
            tariffs=tariffs_list
        )
        result.append(plan_info)

    await cache.set(cache_key, result, expire=3600)
    return result
