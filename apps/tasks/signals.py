from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.tasks.models import Task
from apps.accounts.models import UserProfile


@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Task.objects.get(pk=instance.pk).status
        except Task.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Task)
def update_client_stats(sender, instance, created, **kwargs):
    if created:
        profile = instance.client.profile
        profile.tasks_published += 1
        profile.save(update_fields=['tasks_published', 'updated_at'])


@receiver(post_save, sender=Task)
def update_tasker_stats_on_validate(sender, instance, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    if instance.status == Task.StatusChoices.VALIDATED and old_status != Task.StatusChoices.VALIDATED and instance.assigned_tasker:
        profile = instance.assigned_tasker.profile
        profile.tasks_completed += 1
        profile.update_streak()
        profile.save(update_fields=['tasks_completed', 'updated_at'])
