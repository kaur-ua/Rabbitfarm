from django import forms
from .models import Rabbit, Group
from django.utils.translation import gettext_lazy as _
from datetime import date

class RabbitForm(forms.ModelForm):
    weighing_date = forms.DateField(
    label=_("Weighing date"),
    required=False,
    widget=forms.DateInput(attrs={"type": "date"})
)
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

        self.fields["weighing_date"].initial = date.today()

        self.fields["mother"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

class WeightRecordForm(forms.Form):
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={"type": "date"})
    )

    weight = forms.DecimalField(
        label=_("Weight"),
        max_digits=4,
        decimal_places=2,
        min_value=0.01
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = date.today()

class GroupForm(forms.ModelForm):
    count = forms.IntegerField(min_value=1, label="Кількість")
    class Meta:
        model = Group
        fields = ['name', 'cage_number', 'description']


class SexSeparationForm(forms.Form):
    cage_male = forms.CharField(
        label=_("Male Cage"),
        max_length=20
    )

    cage_female = forms.CharField(
        label=_("Female Cage"),
        max_length=20
    )
