from django import forms
from .models import Rabbit


class RabbitForm(forms.ModelForm):
    class Meta:
        model = Rabbit
        fields = [
            "farm",
            "name",
            "sex",
            "breed",
            "cage",
            "status",
            "birth_date",
            "weight",
            "mother",
            "father",
        ]