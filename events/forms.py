from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    cage = forms.CharField(
        required=False,
        label="Клітка"
    )

    class Meta:
        model = Event
        fields = ['rabbit', 'group', 'event_type', 'date', 'born_alive', 'born_dead', 'note', 'cage']
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'placeholder': 'ДД.ММ.РРРР'
                }
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        rabbit = cleaned_data.get("rabbit")
        group = cleaned_data.get("group") or self.instance.group

        if not rabbit and not group:
            raise forms.ValidationError("Оберіть кролика або групу")

        if rabbit and group:
            raise forms.ValidationError("Оберіть або кролика, або групу")

        return cleaned_data