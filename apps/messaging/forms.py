from django import forms
from django.utils.translation import gettext_lazy as _
from apps.messaging.models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        labels = {'content': ''}
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': _('Écrire un message...'),
                'class': 'form-input',
                'autocomplete': 'off',
            }),
        }
