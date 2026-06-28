from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
from apps.tasks.models import Task
from apps.accounts.models import UserProfile
from apps.reputation.models import Review
from apps.badges.engine import check_and_award_badges


def _check_badges_for_task(task, user):
    """Vérifie les badges pour un utilisateur lié à une tâche."""
    if user and hasattr(user, 'profile'):
        check_and_award_badges(user)


@receiver(post_save, sender=Review)
def recalculate_ratings_on_review(sender, instance, **kwargs):
    if instance.moderation_status != Review.ModerationStatusChoices.VALIDATED:
        return

    if instance.review_type == Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER:
        profile = instance.reviewed.profile
        reviews = Review.objects.filter(
            reviewed=instance.reviewed,
            review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            moderation_status=Review.ModerationStatusChoices.VALIDATED,
        )
        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        profile.tasker_rating_avg = round(float(avg), 2)
        profile.tasker_rating_count = reviews.count()
        profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count', 'updated_at'])

    elif instance.review_type == Review.ReviewTypeChoices.TASKER_REVIEWS_CLIENT:
        profile = instance.reviewed.profile
        reviews = Review.objects.filter(
            reviewed=instance.reviewed,
            review_type=Review.ReviewTypeChoices.TASKER_REVIEWS_CLIENT,
            moderation_status=Review.ModerationStatusChoices.VALIDATED,
        )
        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        profile.client_rating_avg = round(float(avg), 2)
        profile.client_rating_count = reviews.count()
        profile.save(update_fields=['client_rating_avg', 'client_rating_count', 'updated_at'])


@receiver(post_save, sender=Task)
def create_reviews_on_validation(sender, instance, **kwargs):
    if instance.status == Task.StatusChoices.VALIDATED and instance.assigned_tasker:
        if not hasattr(instance, 'review'):
            Review.objects.create(
                task=instance,
                reviewer=instance.client,
                reviewed=instance.assigned_tasker,
                rating=3,
                review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            )
            tasker_profile = instance.assigned_tasker.profile
            reviews = Review.objects.filter(
                reviewed=instance.assigned_tasker,
                review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            )
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
            tasker_profile.tasker_rating_avg = round(float(avg), 2)
            tasker_profile.tasker_rating_count = reviews.count()
            tasker_profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count', 'updated_at'])

            _check_badges_for_task(instance, instance.assigned_tasker)
            _check_badges_for_task(instance, instance.client)


@receiver(post_save, sender=Task)
def check_badges_on_task_status_change(sender, instance, **kwargs):
    """Vérifie les badges à chaque changement de statut de tâche."""
    if instance.status in [
        Task.StatusChoices.ACCEPTED,
        Task.StatusChoices.COMPLETED,
        Task.StatusChoices.VALIDATED,
        Task.StatusChoices.EVALUATED,
    ]:
        if instance.assigned_tasker:
            _check_badges_for_task(instance, instance.assigned_tasker)
        if instance.client:
            _check_badges_for_task(instance, instance.client)
