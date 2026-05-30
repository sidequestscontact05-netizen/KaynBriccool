from django import forms
from django.utils.translation import gettext_lazy as _
from apps.reputation.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': _('Note'),
            'comment': _('Commentaire'),
        }
        widgets = {
            'rating': forms.NumberInput(attrs={'min': '1', 'max': '5', 'class': 'form-input'}),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': _('Partagez votre expérience...'),
                'class': 'form-input',
            }),
        }
