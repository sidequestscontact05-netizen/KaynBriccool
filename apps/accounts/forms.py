from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser, VerificationRecord


class ClientRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label=_('Nom complet'),
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': _('Jean Dupont')}),
    )
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'placeholder': _('jean@exemple.com')}),
    )
    phone_number = forms.CharField(
        label=_('Téléphone'),
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': _('+212 6 12 34 56 78')}),
    )

    class Meta:
        model = CustomUser
        fields = ('full_name', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-input')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Roles.CLIENT
        user.active_role = CustomUser.ActiveRoles.CLIENT
        if commit:
            user.save()
        return user


class TaskerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label=_('Nom complet'),
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': _('Marie Martin')}),
    )
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'placeholder': _('marie@exemple.com')}),
    )
    phone_number = forms.CharField(
        label=_('Téléphone'),
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': _('+212 6 12 34 56 78')}),
    )
    avatar = forms.ImageField(
        label=_('Photo de profil'),
        required=True,
    )
    face_photo_initial_data = forms.CharField(required=False, widget=forms.HiddenInput())
    face_photo_left_data = forms.CharField(required=False, widget=forms.HiddenInput())
    face_photo_right_data = forms.CharField(required=False, widget=forms.HiddenInput())
    face_photo_blink_data = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CustomUser
        fields = ('full_name', 'email', 'phone_number', 'avatar', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-input')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Roles.TASKER
        user.active_role = CustomUser.ActiveRoles.TASKER
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'placeholder': _('votre@email.com'),
            'autofocus': True,
            'class': 'form-input',
        }),
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'placeholder': _('••••••••'),
            'class': 'form-input',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.pop('autofocus', None)


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'placeholder': _('votre@email.com'),
            'autofocus': True,
            'class': 'form-input',
        }),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
    )
    new_password2 = forms.CharField(
        label=_('Confirmer le mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
    )


class PhoneVerificationForm(forms.Form):
    code = forms.CharField(
        label=_('Code de vérification'),
        max_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': _('000000'),
            'maxlength': '6',
            'class': 'form-input',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
        }),
    )


class FaceIdVerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRecord
        fields = [
            'face_photo_initial',
            'face_photo_left',
            'face_photo_right',
            'face_photo_blink',
        ]
        labels = {
            'face_photo_initial': _('Photo initiale'),
            'face_photo_left': _('Visage tourné à gauche'),
            'face_photo_right': _('Visage tourné à droite'),
            'face_photo_blink': _('Photo avec clignement des yeux'),
        }


class ProfileUpdateForm(forms.ModelForm):
    full_name = forms.CharField(
        label=_('Nom complet'),
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    phone_number = forms.CharField(
        label=_('Téléphone'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    avatar = forms.ImageField(
        label=_('Photo de profil'),
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ('full_name', 'phone_number', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-input')


class ProfileForm(forms.ModelForm):
    bio = forms.CharField(
        label=_('Biographie'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-input'}),
    )
    city = forms.CharField(
        label=_('Ville'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = CustomUser
        fields = ('full_name', 'phone_number', 'avatar')
