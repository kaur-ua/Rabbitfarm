from django import forms
from .models import Rabbit, Group, PedigreeNode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
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
        label=_("Mother"),
        required=False,
    )
    father_node = forms.ModelChoiceField(
        queryset=PedigreeNode.objects.none(),
        label=_("Father"),
        required=False,
    )

    class Meta:
        model = Rabbit
        fields = [

                "group",
                "name",
                "origin_source",
                "mother_manual",
                "father_manual",
                "sex",
                "breed",
                "conditional_class",
                "cage",
                "status",
                "birth_date",
                "weight",
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
        self.farm = farm
        super().__init__(*args, **kwargs)

        if not self.is_bound and self.instance.pk and get_language() == "uk":
            self.initial["breed"] = BREED_TRANSLATIONS.get(
                self.instance.breed,
                self.instance.breed,
            )

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

        from rabbits.services import find_duplicate_parents

        breed = cleaned_data.get("breed") or ""
        origin = (cleaned_data.get("origin_source") or "").strip()

        parents = [
            ("mother_manual", "mother_node", "F", _("Mother")),
            ("father_manual", "father_node", "M", _("Father")),
        ]

        for name_field, node_field, sex, label in parents:
            parent_name = (cleaned_data.get(name_field) or "").strip()
            selected_node = cleaned_data.get(node_field)

            if selected_node:
                cleaned_data[name_field] = ""
                continue

            if not parent_name:
                continue

            matches = find_duplicate_parents(
                self.farm,
                parent_name,
                sex,
                breed,
                origin,
            )

            if matches.exists():
                self.add_error(
                    node_field,
                    _("Select an existing matching parent from the list."),
                )

        return cleaned_data

    

    def save_pedigree(self):
        rabbit = self.instance

        parent_breed = (rabbit.breed or "").strip()
        if "невідом" in parent_breed.lower() or "unknown" in parent_breed.lower():
            parent_breed = ""

        mother_node = self.cleaned_data.get("mother_node")
        father_node = self.cleaned_data.get("father_node")

        mother_name = (self.cleaned_data.get("mother_manual") or "").strip()
        father_name = (self.cleaned_data.get("father_manual") or "").strip()

        if not mother_node and mother_name:
            mother_node = PedigreeNode.objects.create(
                farm=rabbit.farm,
                manual_name=mother_name,
                manual_sex="F",
                manual_breed=parent_breed,
                origin_farm=rabbit.origin_source,
                is_manual=True,
            )

        if not father_node and father_name:
            father_node = PedigreeNode.objects.create(
                farm=rabbit.farm,
                manual_name=father_name,
                manual_sex="M",
                manual_breed=parent_breed,
                origin_farm=rabbit.origin_source,
                is_manual=True,
            )

        pedigree_node, _ = PedigreeNode.objects.get_or_create(
            rabbit=rabbit,
            defaults={
                "is_manual": False,
                "farm": rabbit.farm,
            },
        )

        pedigree_node.farm = rabbit.farm
        pedigree_node.mother = mother_node
        pedigree_node.father = father_node

        pedigree_node.save(
            update_fields=["farm", "mother", "father"]
        )

        rabbit.mother = mother_node.rabbit if mother_node else None
        rabbit.father = father_node.rabbit if father_node else None

        rabbit.save(update_fields=["mother", "father"])

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
