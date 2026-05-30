from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect


class AccountAdapter(DefaultAccountAdapter):
    """Prevent email/password signup — only Google signup allowed."""

    def is_open_for_signup(self, request):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.full_name:
            name = data.get('name') or ' '.join(filter(None, [data.get('given_name'), data.get('family_name')]))
            if name:
                user.full_name = name.strip()
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        user.full_name = sociallogin.account.extra_data.get('name', user.full_name or 'Utilisateur')
        user.save(update_fields=['full_name'])
        return user
