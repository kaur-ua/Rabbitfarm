from django import forms
from .models import Rabbit, Group


class RabbitForm(forms.ModelForm):
    class Meta:
        model = Rabbit
        fields = [
            
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
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mother"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

        self.fields["father"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

class GroupForm(forms.ModelForm):
    count = forms.IntegerField(min_value=1, label="Кількість")
    class Meta:
        model = Group
        fields = ['name', 'cage_number', 'description']