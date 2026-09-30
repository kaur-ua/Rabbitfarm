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



from .models import RabbitBreed


@admin.register(RabbitBreed)
class RabbitBreedAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "conditional_class",
        "first_mating_age_months",
        "first_mating_weight_kg",
    )
    list_filter = ("conditional_class",)
    search_fields = ("name",)
