from django import template
from django.utils.translation import get_language
from rabbits.breed_translations import BREED_TRANSLATIONS

register = template.Library()



@register.filter
def breed_name(value):
    if get_language() == "uk":
        return BREED_TRANSLATIONS.get(value, value)
    return value
