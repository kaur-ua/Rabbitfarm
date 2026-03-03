from datetime import timedelta
from events.models import FarmEvent
from rabbits.models import Rabbit


def generate_kindling_events():
    females = Rabbit.objects.filter(sex="F", status="ACTIVE")

    for rabbit in females:
        last_mating = (
            rabbit.events
            .filter(event_type="MATING")
            .order_by("-date")
            .first()
        )

        if not last_mating:
            continue

        kindling_after_mating = rabbit.events.filter(
            event_type="KINDLING",
            date__gte=last_mating.date
        ).exists()

        if kindling_after_mating:
            FarmEvent.objects.filter(
                farm=rabbit.farm,
                entity_type="rabbit",
                entity_id=rabbit.id,
                event_type__in=["nest_check", "kindling"],
                status="pending"
            ).update(status="done")

            continue

        nest_date = last_mating.date + timedelta(days=25)
        kindling_date = last_mating.date + timedelta(days=28)

        FarmEvent.objects.update_or_create(
            farm=rabbit.farm,
            entity_type="rabbit",
            entity_id=rabbit.id,
            event_type="nest_check",
            defaults={
                "due_date": nest_date,
                "auto_generated": True,
                "status": "pending",
            },
        )

        FarmEvent.objects.update_or_create(
            farm=rabbit.farm,
            entity_type="rabbit",
            entity_id=rabbit.id,
            event_type="kindling",
            defaults={
                "due_date": kindling_date,
                "auto_generated": True,
                "status": "pending",
            },
        )