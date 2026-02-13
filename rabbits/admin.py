from django.contrib import admin
from .models import Rabbit


@admin.register(Rabbit)
class RabbitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sex", "birth_date", "owner")
    list_filter = ("sex",)
    search_fields = ("name",)



