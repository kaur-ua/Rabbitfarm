from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['rabbit', 'event_type', 'date', 'born_alive', 'born_dead', 'note']