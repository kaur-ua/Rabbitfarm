from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("rabbit", "event_type", "date", "next_action", "status")
    search_fields = ("rabbit__name", "event_type")
