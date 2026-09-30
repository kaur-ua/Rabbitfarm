from django.core.management.base import BaseCommand
from rabbits.models import RabbitBreed

BREEDS = [
    ("New Zealand White", "medium", 4.5, 3.4),
    ("New Zealand Red", "medium", 4.5, 3.4),
    ("New Zealand Black", "medium", 4.5, 3.4),
    ("New Zealand Blue", "medium", 4.5, 3.4),
    ("Californian", "medium", 4.5, 3.4),
    ("Chinchilla", "medium", 4.5, 3.4),
    ("Rex", "medium", 4.5, 3.4),
    ("Satin", "medium", 4.5, 3.4),
    ("Vienna Blue", "medium", 4.5, 3.4),
    ("Vienna White", "medium", 4.5, 3.4),
    ("Vienna Black", "medium", 4.5, 3.4),
    ("Vienna Grey", "medium", 4.5, 3.4),
    ("Flemish Giant", "large", 6.0, 4.3),
    ("French Lop", "large", 6.0, 4.3),
    ("Giant Chinchilla", "large", 6.0, 4.3),
    ("Checkered Giant", "large", 6.0, 4.3),
    ("American Chinchilla", "large", 6.0, 4.3),
    ("Champagne d’Argent", "large", 6.0, 4.3),
    ("Large Light Silver (LLS) — БСС / Велике світле срібло", "large", 6.0, 4.3),
    ("Poltava Silver / Полтавське срібло", "large", 6.0, 4.3),
    ("Silver Fox", "large", 6.0, 4.3),
    ("Beveren", "large", 6.0, 4.3),
    ("Giant Angora", "large", 6.0, 4.3),
    ("English Lop", "large", 6.0, 4.3),
    ("Polish", "decorative", 5.0, 2.0),
    ("Netherland Dwarf", "decorative", 5.0, 2.0),
    ("Holland Lop", "decorative", 5.0, 2.0),
    ("Mini Rex", "decorative", 5.0, 2.0),
    ("Dwarf Hotot", "decorative", 5.0, 2.0),
    ("Lionhead", "decorative", 5.0, 2.0),
    ("Jersey Wooly", "decorative", 5.0, 2.0),
    ("American Fuzzy Lop", "decorative", 5.0, 2.0),
    ("Britannia Petite", "decorative", 5.0, 2.0),
    ("Mini Lop", "decorative", 5.0, 2.0),
    ("Florida White", "decorative", 5.0, 2.0),
]

class Command(BaseCommand):
    help = "Load initial RabbitFarm breed data"

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for name, breed_class, age, weight in BREEDS:
            _, was_created = RabbitBreed.objects.update_or_create(
                name=name,
                defaults={
                    "conditional_class": breed_class,
                    "first_mating_age_months": age,
                    "first_mating_weight_kg": weight,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Додано: {created}; оновлено: {updated}; "
                f"у списку: {len(BREEDS)}"
            )
        )
