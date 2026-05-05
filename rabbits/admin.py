from django.contrib import admin
from .models import Rabbit, Group

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

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cage_number",
        "description",
    )

