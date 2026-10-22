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

def get_pairing_candidates(farm):
    """
    Повертає активних самців і самок одного господарства.
    Готовність до парування перевіряється окремо.
    """
    from rabbits.models import Rabbit

    rabbits = Rabbit.objects.filter(
        farm=farm,
        status="ACTIVE",
        sex__in=("F", "M"),
    ).select_related(
        "mother",
        "father",
    ).order_by("inventory_number")

    females = rabbits.filter(sex="F")
    males = rabbits.filter(sex="M")

    return females, males

def _get_ancestors(rabbit, max_depth=3):
    """Збирає відомих предків і перевіряє повноту родоводу."""
    ancestors = {}
    frontier = [(rabbit, 0)]
    visited = {rabbit.pk}
    pedigree_complete = True

    while frontier:
        current, depth = frontier.pop(0)

        if depth >= max_depth:
            if current.mother_id or current.father_id:
                pedigree_complete = False
            continue

        if (
            not current.mother_id
            or not current.father_id
            or current.mother_manual
            or current.father_manual
        ):
            pedigree_complete = False

        for parent in (current.mother, current.father):
            if parent is None or parent.pk in visited:
                continue

            visited.add(parent.pk)
            ancestors[parent.pk] = depth + 1
            frontier.append((parent, depth + 1))

    return ancestors, pedigree_complete


def check_pair_relatedness(female, male):
    """
    Перевіряє спільних предків до трьох поколінь.
    Неповний родовід повертає unknown.
    """
    if female.pk == male.pk:
        return "same_rabbit"

    female_ancestors, female_complete = _get_ancestors(female)
    male_ancestors, male_complete = _get_ancestors(male)

    if set(female_ancestors) & set(male_ancestors):
        return "related"

    if not female_complete or not male_complete:
        return "unknown"

    return "no_known_relation"

def evaluate_pairing(female, male):
    """
    Оцінює пару кролів за спорідненістю.
    Неповний родовід не блокує рекомендацію,
    але додає попередження.
    """
    if female.pk == male.pk:
        return {
            "recommended": False,
            "relatedness": "same_rabbit",
            "warnings": ["Не можна рекомендувати кролика самому собі."],
        }

    if female.sex != "F" or male.sex != "M":
        return {
            "recommended": False,
            "relatedness": "invalid_sex",
            "warnings": ["Для пари потрібні самка та самець."],
        }

    if female.farm_id != male.farm_id:
        return {
            "recommended": False,
            "relatedness": "different_farm",
            "warnings": ["Кролі належать до різних господарств."],
        }

    if female.status != "ACTIVE" or male.status != "ACTIVE":
        return {
            "recommended": False,
            "relatedness": "inactive",
            "warnings": ["Обидва кролі мають бути активними."],
        }

    relatedness = check_pair_relatedness(female, male)
    warnings = []

    if relatedness == "related":
        warnings.append("Виявлено спільних предків.")
        return {
            "recommended": False,
            "relatedness": relatedness,
            "warnings": warnings,
        }

    female_breed = (female.breed or "").strip()
    male_breed = (male.breed or "").strip()

    unknown_breeds = {"", "unknown", "невідома", "невідомо"}

    female_breed_unknown = female_breed.casefold() in unknown_breeds
    male_breed_unknown = male_breed.casefold() in unknown_breeds

    if female_breed_unknown or male_breed_unknown:
        warnings.append(
            "Можливе міжпородне схрещування. "
            "Потомство може бути кросовим. "
            "Чистопородність майбутніх кроленят не гарантована."
        )
    elif female_breed.casefold() != male_breed.casefold():
        warnings.append(
            "Можливе міжпородне схрещування. "
            "Потомство може бути кросовим. "
            "Чистопородність майбутніх кроленят не гарантована."
        )
        return {
            "recommended": False,
            "relatedness": relatedness,
            "warnings": warnings,
        }


    return {
        "recommended": True,
        "relatedness": relatedness,
        "warnings": warnings,
}
def get_recommended_pairs(farm):
    """
    Формує рекомендовані пари активних кролів.
    Перевіряє спорідненість і готовність до першого парування.
    """
    females, males = get_pairing_candidates(farm)
    recommended_pairs = []

    for female in females:
        for male in males:
            evaluation = evaluate_pairing(female, male)

            if not evaluation["recommended"]:
                continue

            warnings = list(evaluation["warnings"])

            for rabbit in (female, male):
                has_mating_event = rabbit.events.filter(
                    event_type="mating"
                ).exists()

                # Якщо парування вже було, повторно готовність
                # до першого парування не перевіряємо.
                if has_mating_event:
                    continue

                readiness = get_mating_readiness(rabbit)

                if readiness == NOT_READY:
                    evaluation["recommended"] = False
                    break

                if readiness == INSUFFICIENT_DATA:
                    warning = (
                        f"{rabbit.name}: недостатньо даних "
                        "для оцінки готовності до першого парування."
                    )
                    if warning not in warnings:
                        warnings.append(warning)

                elif readiness is None:
                    # Оцінювання ще не почалося: кролик надто молодий.
                    evaluation["recommended"] = False
                    break

            if not evaluation["recommended"]:
                continue

            recommended_pairs.append({
                "female": female,
                "male": male,
                "relatedness": evaluation["relatedness"],
                "warnings": warnings,
            })

    return recommended_pairs