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
            "mother_manual",
            "father",
            "father_manual",
            "photo",
        ]

        widgets = {
    "birth_date": forms.DateInput(
        attrs={"type": "date"}
    )
    }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["mother"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

        self.fields["father"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

        self.fields["mother_manual"].label = "Мати (вручну)"
        self.fields["father_manual"].label = "Батько (вручну)"

class GroupForm(forms.ModelForm):
    count = forms.IntegerField(min_value=1, label="Кількість")
    class Meta:
        model = Group
        fields = ['name', 'cage_number', 'description']
        
        
class SexSeparationForm(forms.Form):
    cage_male = forms.CharField(
        label="Клітка для самців",
        max_length=20
    )

    cage_female = forms.CharField(
        label="Клітка для самок",
        max_length=20
    )