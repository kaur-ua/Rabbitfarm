import uuid
from django.db import models


class FarmEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    farm = models.ForeignKey(
        "farms.Farm",
        on_delete=models.CASCADE,
        related_name="events"
    )

    entity_type = models.CharField(max_length=20)
    entity_id = models.UUIDField()

    event_type = models.CharField(max_length=50)

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    auto_generated = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["farm", "entity_type", "entity_id", "event_type"],
                condition=models.Q(status="pending"),
                name="farm_events_unique_active"
            )
        ]

    def __str__(self):
        return f"{self.event_type} ({self.status})"
