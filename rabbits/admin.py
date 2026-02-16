from django.contrib import admin
from .models import Rabbit, Event


class EventInline(admin.TabularInline):
    model = Event
    extra = 1


@admin.register(Rabbit)
class RabbitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sex", "birth_date", "owner")
    list_display_links = ("name",)

    list_filter = ("sex",)
    search_fields = ("name",)

    inlines = [EventInline]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "rabbit", "event_type", "date")
    list_filter = ("event_type",)




