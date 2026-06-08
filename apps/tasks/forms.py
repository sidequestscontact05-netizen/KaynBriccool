from django import forms
from django.utils.translation import gettext_lazy as _
from apps.tasks.models import Task, TaskProof, SubCategory


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'category',
            'subcategory',
            'description',
            'reward',
            'arrival_address',
            'has_route',
            'proof_required',
            'departure_address',
            'deadline',
        ]
        labels = {
            'category': _('Catégorie'),
            'subcategory': _('Sous-catégorie'),
            'description': _('Description'),
            'reward': _('Rémunération (Dh)'),
            'has_route': _('Task avec trajet'),
            'proof_required': _('Preuve photo requise'),
            'departure_address': _('Adresse de départ'),
            'arrival_address': _('Adresse d\'arrivée'),
            'deadline': _('Date limite'),
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'subcategory': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Ajouter une petite description...'), 'class': 'form-input'}),
            'reward': forms.NumberInput(attrs={'placeholder': '25.00', 'min': '1', 'step': '0.01', 'class': 'form-input'}),
            'has_route': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'proof_required': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'departure_address': forms.TextInput(attrs={'placeholder': _('Adresse de départ'), 'class': 'form-input'}),
            'arrival_address': forms.TextInput(attrs={'placeholder': _('Adresse d\'arrivée'), 'class': 'form-input'}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].required = False
        if self.data and self.data.get('category'):
            category_id = self.data.get('category')
        elif self.instance and self.instance.pk and self.instance.category_id:
            category_id = self.instance.category_id
        else:
            category_id = None
        if category_id:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(
                category_id=category_id, is_active=True
            )
        else:
            self.fields['subcategory'].queryset = SubCategory.objects.none()

    def clean_reward(self):
        reward = self.cleaned_data.get('reward')
        if reward and reward <= 0:
            raise forms.ValidationError(_('La rémunération doit être supérieure à 0.'))
        return reward

    def clean(self):
        cleaned_data = super().clean()
        # Handle coordinates manually from POST data to bypass DecimalField validation
        for field_name in ['arrival_lat', 'arrival_lng', 'departure_lat', 'departure_lng']:
            val = self.data.get(field_name)
            if val:
                try:
                    cleaned_data[field_name] = float(val)
                except (ValueError, TypeError):
                    cleaned_data[field_name] = None
        return cleaned_data


class TaskProofForm(forms.Form):
    def __init__(self, *args, **kwargs):
        proof_required = kwargs.pop('proof_required', False)
        super().__init__(*args, **kwargs)
        if proof_required:
            self.fields['photos'].required = True

    description = forms.CharField(
        label=_('Description de la réalisation'),
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': _('Décrivez ce que vous avez fait...'),
            'class': 'form-input',
        }),
    )
    photos = forms.FileField(
        label=_('Photos de preuve'),
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-input'}),
    )


class ProofReviewForm(forms.Form):
    action = forms.ChoiceField(
        label=_('Action'),
        choices=[
            ('accept', _('Valider')),
            ('revision', _('Demander une modification')),
            ('reject', _('Refuser')),
            ('litige', _('Ouvrir un litige')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
    )
    notes = forms.CharField(
        label=_('Notes'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Raison de la demande de modification ou du refus...'),
            'class': 'form-input',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('notes')
        if action == 'revision' and not notes:
            raise forms.ValidationError({'notes': _('Les notes sont obligatoires pour demander une modification.')})
        return cleaned_data


class TaskApplicationForm(forms.Form):
    message = forms.CharField(
        label=_('Message au client'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Présentez-vous brièvement et expliquez pourquoi vous êtes le bon tasker...'),
            'class': 'form-input',
        }),
    )
