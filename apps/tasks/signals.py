from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.tasks.models import Task
from apps.accounts.models import UserProfile


@receiver(post_save, sender=Task)
def update_client_stats(sender, instance, created, **kwargs):
    if created:
        profile = instance.client.profile
        profile.tasks_published += 1
        profile.save(update_fields=['tasks_published', 'updated_at'])


@receiver(post_save, sender=Task)
def update_tasker_stats_on_validate(sender, instance, **kwargs):
    if instance.status == Task.StatusChoices.VALIDATED and instance.assigned_tasker:
        profile = instance.assigned_tasker.profile
        profile.tasks_completed += 1
        profile.update_streak()
        profile.save(update_fields=['tasks_completed', 'updated_at'])


@receiver(post_save, sender=Task)
def update_client_streak(sender, instance, created, **kwargs):
    if created:
        instance.client.profile.update_streak()
