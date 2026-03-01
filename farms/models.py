from django.conf import settings
from django.db import models


class Farm(models.Model):
    name = models.CharField(max_length=200)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
