from django.db import models
from django.contrib.auth.models import User
from farms.models import Farm




class Rabbit(models.Model):
    farm = models.ForeignKey(
         Farm,
         on_delete=models.CASCADE,
         related_name="rabbits"
    )
    SEX_CHOICES = [
         ("F", "Самка"),
         ("M", "Самець"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Активний"),
        ("SOLD", "Проданий"),
        ("CULLED", "Вибракований"),
    ]

    

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


