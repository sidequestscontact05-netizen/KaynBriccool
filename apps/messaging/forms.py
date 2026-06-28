from django import forms
from django.utils.translation import gettext_lazy as _
from apps.messaging.models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file']
        labels = {'content': '', 'file': ''}
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': _('Écrire un message...'),
                'class': 'form-input',
                'autocomplete': 'off',
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.zip,.txt',
            }),
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            if f.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('Le fichier ne doit pas dépasser 10 Mo.'))
        return f
