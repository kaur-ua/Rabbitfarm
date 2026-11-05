from django import forms
from .models import Rabbit, Group, PedigreeNode
from django.utils.translation import gettext_lazy as _
from datetime import date
from rabbits.breed_translations import BREED_TRANSLATIONS
from django.db.models import Q

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
    widget=forms.DateInput(attrs={"type": "date"}),
    )
    mother_node = forms.ModelChoiceField(
        queryset=PedigreeNode.objects.none(),
        label=_("Mother from pedigree"),
        required=False,
    )
    father_node = forms.ModelChoiceField(
        queryset=PedigreeNode.objects.none(),
        label=_("Father from pedigree"),
        required=False,
    )

    class Meta:
        model = Rabbit
        fields = [

            "group",
            "name",
            "origin_source",
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
        farm = kwargs.pop("farm", None)
        super().__init__(*args, **kwargs)

        self.fields["mother"].required = False
        self.fields["father"].required = False

        nodes = PedigreeNode.objects.filter(farm=farm) if farm else PedigreeNode.objects.none()

        self.fields["mother_node"].queryset = nodes.filter(
            Q(rabbit__sex="F") | Q(rabbit__isnull=True, manual_sex="F")
        )

        self.fields["father_node"].queryset = nodes.filter(
            Q(rabbit__sex="M") | Q(rabbit__isnull=True, manual_sex="M")
        )

        if self.instance.pk:
            pedigree_node = PedigreeNode.objects.filter(
                rabbit=self.instance
            ).first()

            if pedigree_node:
                self.initial["mother_node"] = pedigree_node.mother_id
                self.initial["father_node"] = pedigree_node.father_id

        self.fields["weighing_date"].initial = date.today()

    def clean_breed(self):
        breed = self.cleaned_data.get("breed", "").strip()

        reverse_translations = {
            translated: original
            for original, translated in BREED_TRANSLATIONS.items()
        }

        return reverse_translations.get(breed, breed)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save_pedigree(self):
        rabbit = self.instance

        pedigree_node, _ = PedigreeNode.objects.get_or_create(
            rabbit=rabbit,
            defaults={
                "is_manual": False,
                "farm": rabbit.farm,
            },
        )

        if pedigree_node.farm_id != rabbit.farm_id:
            pedigree_node.farm = rabbit.farm

        pedigree_node.mother = self.cleaned_data.get("mother_node")
        pedigree_node.father = self.cleaned_data.get("father_node")

        pedigree_node.save(
            update_fields=["farm", "mother", "father"]
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
