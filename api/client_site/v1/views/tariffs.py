from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List

from ..serializers.tariffs import PlanInfo, TariffInfo, FeatureItemInfo, FeatureInfo
from models import TariffCategory
from services.cache_service import cache
from utils.i18n import get_translation

router = APIRouter()


def _translate(obj, field: str, lang: str) -> str:
    """Get translated field or fallback."""
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, field, "") or ""


@router.get("/", response_model=List[PlanInfo])
async def list_plans(
    request: Request,
    t: dict = Depends(get_translation),
):
    lang = request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0].lower()
    if lang not in {"en", "ru", "uz"}:
        raise HTTPException(status_code=400, detail="Unsupported language")

    cache_key = f"plans_{lang}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    categories = await TariffCategory.filter(is_active=True)
    result = []

    for category in categories:
        category_name = getattr(category, f"name_{lang}", None) or category.name
        tariffs = await Tariff.filter(category_id=category.id, is_active=True).prefetch_related("tariff_features__feature")

        tariffs_list = []
        for tariff in tariffs:
            t_name = getattr(tariff, f"name_{lang}", None) or tariff.name
            t_desc = getattr(tariff, f"description_{lang}", None) or tariff.description

            features_list = []
            for tf in tariff.tariff_features:
                feat = tf.feature
                if not feat:
                    continue
                f_name = getattr(feat, f"name_{lang}", None) or feat.name
                f_desc = getattr(feat, f"description_{lang}", None) or feat.description
                features_list.append(FeatureItemInfo(
                    id=tf.id,
                    tariff=tariff.id,
                    is_included=tf.is_included,
                    feature=FeatureInfo(
                        id=feat.id,
                        name=f_name,
                        description=f_desc
                    )
                ))

            tariffs_list.append(TariffInfo(
                id=tariff.id,
                name=t_name,
                old_price=tariff.old_price,
                price=tariff.price,
                description=t_desc,
                tokens=tariff.tokens,
                duration=tariff.duration,
                features=features_list,
                is_default=tariff.is_default,
                redirect_url=None,
            ))

        result.append(PlanInfo(
            id=category.id,
            name=category_name,
            sale=float(category.sale),
            tariffs=tariffs_list
        ))

    await cache.set(cache_key, result, 3600)
    return result
