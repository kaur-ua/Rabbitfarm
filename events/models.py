from django.db import models

class Event(models.Model):

    EVENT_TYPES = [
        ("mating", "Злучка"),
        ("kindling", "Окрол"),
        ("vaccination", "Вакцинація"),
        ("weaning", "Відсадка"),
    ]
 
    rabbit = models.ForeignKey(
        "rabbits.Rabbit",
        on_delete=models.CASCADE,
        related_name="events"
    )

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES
    )

    date = models.DateField()

    next_action = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    note = models.CharField(
        max_length=200,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.rabbit} - {self.event_type} ({self.date})"

