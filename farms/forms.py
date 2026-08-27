from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Farm


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['name', 'location', 'phone', 'description', 'image']

        labels = {
            'name': _('Farm Name'),
            'location': _('Location'),
            'phone': _('Phone'),
            'description': _('Description'),
            'image': _('Farm Photo'),
        }