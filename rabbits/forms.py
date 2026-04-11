from django import forms
from .models import Rabbit, Group


class RabbitForm(forms.ModelForm):
    class Meta:
        model = Rabbit
        fields = [
            "farm",
            "group",
            "name",
            "sex",
            "breed",
            "cage",
            "status",
            "birth_date",
            "weight",
            "mother",
            "father",
            "photo",
        ]


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'cage_number', 'description']