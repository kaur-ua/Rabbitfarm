from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from rabbits.models import RabbitBreed


READY = "Готовий до парування"
NOT_READY = "Не готовий до парування"
INSUFFICIENT_DATA = "Недостатньо даних для аналізу"


def _add_months(start_date, months):
    """Додає цілу кількість календарних місяців до дати."""
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _mating_age_date(birth_date, age_months):
    """Обчислює дату досягнення заданого віку в місяцях."""
    age_months = Decimal(str(age_months))
    whole_months = int(age_months)
    fractional_month = age_months - whole_months

    threshold_date = _add_months(birth_date, whole_months)
    extra_days = round(fractional_month * Decimal("30.4375"))

    return threshold_date + timedelta(days=extra_days)


def _get_thresholds(rabbit):
    """Повертає пороги відомої породи або заданого умовного класу."""
    breed_name = (rabbit.breed or "").strip()

    aliases = {
        "віденський голубий": "Vienna Blue",
    }
    lookup_name = aliases.get(breed_name.casefold(), breed_name)
    breed = RabbitBreed.objects.filter(name__iexact=lookup_name).first()

    if breed:
        return (
            breed.first_mating_age_months,
            breed.first_mating_weight_kg,
        )

    if rabbit.conditional_class not in ("medium", "large"):
        return None

    breed = RabbitBreed.objects.filter(
        conditional_class=rabbit.conditional_class
    ).first()

    if not breed:
        return None

    return (
        breed.first_mating_age_months,
        breed.first_mating_weight_kg,
    )


def get_mating_readiness(rabbit, today=None):
    """
    Повертає статус готовності до першого парування.
    До початку перевірки повертає None.
    """
    today = today or date.today()

    if not rabbit.birth_date or rabbit.sex not in ("F", "M"):
        return INSUFFICIENT_DATA

    if rabbit.events.filter(event_type="mating").exists():
        return None

    thresholds = _get_thresholds(rabbit)

    if thresholds is None:
        return INSUFFICIENT_DATA

    minimum_age_months, minimum_weight = thresholds
    threshold_date = _mating_age_date(
        rabbit.birth_date,
        minimum_age_months,
    )

    # Починаємо оцінювання за 10 днів до мінімального віку.
    if today < threshold_date - timedelta(days=10):
        return None

    if rabbit.weight is None:
        return INSUFFICIENT_DATA

    if today < threshold_date or rabbit.weight < minimum_weight:
        return NOT_READY

    return READY
