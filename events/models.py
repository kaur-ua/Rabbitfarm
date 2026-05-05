from django.db import models
from datetime import timedelta

class Event(models.Model):

    EVENT_TYPES = [
    ("mating", "Злучка"),
    ("kindling", "Окрол"),
    ("vaccination", "Вакцинація"),
    ("weaning", "Відсадка"),
    ("split", "Розділення за статтю"),
]
 
    rabbit = models.ForeignKey(
    "rabbits.Rabbit",
    on_delete=models.CASCADE,
    related_name="events",
    null=True,
    blank=True
    )
    

    group = models.ForeignKey(
    "rabbits.Group",
    on_delete=models.CASCADE,
    related_name="events",
    null=True,
    blank=True
)

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES
    )

    date = models.DateField()
    next_action_date = models.DateField(
        null=True,
        blank=True
    )

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

    born_alive = models.PositiveIntegerField(null=True, blank=True)
    born_dead = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.event_type == "mating":
            self.next_action_date = self.date + timedelta(days=28)
            self.next_action = "Окрол"

        elif self.event_type == "kindling":
            self.next_action_date = self.date + timedelta(days=60)
            self.next_action = "Відсадка"

        elif self.event_type == "weaning":
            self.next_action_date = self.date + timedelta(days=30)
            self.next_action = "Розділення за статтю"

        else:
            # щоб не залишалося старих значень
            self.next_action = None
            self.next_action_date = None

        super().save(*args, **kwargs)
