from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    cage = forms.CharField(
        required=False,
        label="Клітка"
    )
    class Meta:
        model = Event
        fields = ['rabbit', 'event_type', 'date', 'born_alive', 'born_dead', 'note', 'cage']
        widgets = {
        'date': forms.DateInput(
        attrs={
           'type': 'date',
           'placeholder': 'ДД.ММ.РРРР'
                }
            )
        }