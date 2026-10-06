from django import forms
from .models import Rabbit, Group
from django.utils.translation import gettext_lazy as _
from datetime import date
from rabbits.breed_translations import BREED_TRANSLATIONS

class RabbitForm(forms.ModelForm):
    CONDITIONAL_CLASS_CHOICES = [
        ("medium", _("Medium class")),
        ("large", _("Large class")),
    ]

    conditional_class = forms.ChoiceField(
        choices=CONDITIONAL_CLASS_CHOICES,
        label=_("Estimated class"),
        required=False,
        widget=forms.RadioSelect,
    )
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
            "conditional_class",
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
    format="%Y-%m-%d",
    attrs={"type": "date"},
),
    "breed": forms.TextInput(
        attrs={
            "list": "breed-suggestions",
            "autocomplete": "off",
        }
    ),
}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["weighing_date"].initial = date.today()

        self.fields["mother"].label_from_instance = (
            lambda obj: f"{obj.inventory_number} | {obj.name}"
        )

    def clean_breed(self):
        breed = self.cleaned_data.get("breed", "").strip()

        reverse_translations = {
            translated: original
            for original, translated in BREED_TRANSLATIONS.items()
        }

        return reverse_translations.get(breed, breed)

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
