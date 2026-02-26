from django.db import models
from django.contrib.auth.models import User


class Rabbit(models.Model):
    SEX_CHOICES = [
        ("F", "Самка"),
        ("M", "Самець"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Активний"),
        ("SOLD", "Проданий"),
        ("CULLED", "Вибракований"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rabbits"
    )

    name = models.CharField(max_length=100)
    inventory_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Інвентарний номер"
    ) 
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES
    )

    breed = models.CharField(max_length=100, blank=True)

    cage = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    mother = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_mother"
    )

    father = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children_from_father"
    )

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    EVENT_TYPES = [
        ("VACCINATION", "Вакцинація"),
        ("MATING", "Парування"),
        ("KINDLING", "Окрол"),
        ("TREATMENT", "Лікування"),
        ("NOTE", "Нотатка"),
    ]

    rabbit = models.ForeignKey(
        Rabbit,
        on_delete=models.CASCADE,
        related_name="events"
    )

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES
    )

    date = models.DateField()

    notes = models.TextField(blank=True)

    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_events"
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    kits_count = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rabbit.name} — {self.get_event_type_display()} ({self.date})"
