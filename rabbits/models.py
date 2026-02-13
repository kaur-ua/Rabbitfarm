from django.db import models
from django.contrib.auth.models import User


class Rabbit(models.Model):
    SEX_CHOICES = [
        ("F", "Самка"),
        ("M", "Самець"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rabbits"
    )

    name = models.CharField(max_length=100)

    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES
    )

    birth_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

