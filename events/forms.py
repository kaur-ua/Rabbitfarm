from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    cage = forms.CharField(
        required=False,
        label="Cage"
    )

    class Meta:
        model = Event
        fields = [
    'rabbit', 'male', 'group', 'event_type', 'date',
    'born_alive', 'born_dead', 'note', 'cage'
]
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'placeholder': 'YYYY-MM-DD'
                }
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        rabbit = cleaned_data.get("rabbit")
        male = cleaned_data.get("male")
        group = cleaned_data.get("group") or self.instance.group
        event_type = cleaned_data.get("event_type")

        if not rabbit and not group:
            raise forms.ValidationError("Select a rabbit or a group")

        if rabbit and group:
            raise forms.ValidationError("Select either a rabbit or a group")

        if event_type == "mating" and not male:
            self.add_error("male", "Select a male for mating")

        return cleaned_data