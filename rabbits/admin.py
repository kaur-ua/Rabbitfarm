from django.contrib import admin
from .models import Rabbit

@admin.register(Rabbit)
class RabbitAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "inventory_number",
        "sex",
        "weight",
        "breed",
        "status",
    )

