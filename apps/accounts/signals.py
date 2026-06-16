from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(user_logged_in)
def update_streak_on_login(sender, request, user, **kwargs):
    if hasattr(user, 'profile'):
        user.profile.update_streak()
        if user.is_tasker() and not user.profile.welcome_modal_shown:
            request.session['show_welcome_modal'] = True
