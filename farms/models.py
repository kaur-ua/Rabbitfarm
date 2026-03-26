from django.conf import settings
from django.db import models


class Farm(models.Model):

    name = models.CharField(
    max_length=200,
    verbose_name="Назва ферми"
)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms"
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Місцезнаходження"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Опис"
    )

    image = models.ImageField(
        upload_to="farm_images/",
        blank=True,
        null=True,
        verbose_name="Фото ферми"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name
