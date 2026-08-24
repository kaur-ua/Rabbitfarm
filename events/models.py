from django.db import models
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

class Event(models.Model):

    EVENT_TYPES = [
    ("mating", _("Mating")),
    ("kindling", _("Kindling")),
    ("vaccination", _("Vaccination")),
    ("weaning", _("Weaning")),
    ("split", _("Separate by Sex")),
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
            self.next_action = "Kindling"

        elif self.event_type == "kindling":
            self.next_action_date = self.date + timedelta(days=60)
            self.next_action = "Weaning"

        elif self.event_type == "weaning":
            self.next_action_date = self.date + timedelta(days=30)
            self.next_action = "Separate by Sex"

        else:
            # щоб не залишалося старих значень
            self.next_action = None
            self.next_action_date = None

        super().save(*args, **kwargs)

    def get_next_action_display(self):
        translations = {
            "Kindling": _("Kindling"),
            "Weaning": _("Weaning"),
            "Separate by Sex": _("Separate by Sex"),
        }
        return translations.get(self.next_action, self.next_action)
