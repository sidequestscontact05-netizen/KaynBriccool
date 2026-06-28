from django.db import models
from django.db.models import Count
from django.utils import timezone
from apps.badges.models import Badge, UserBadge
from apps.accounts.models import UserProfile
from apps.tasks.models import Task
from apps.reputation.models import Review


def check_and_award_badges(user):
    """Vérifie et attribue tous les badges que l'utilisateur a mérités."""
    if not hasattr(user, 'profile'):
        return

    profile = user.profile
    badges_to_award = []

    eligible_badges = Badge.objects.filter(is_active=True)

    if user.is_tasker() or user.role == 'both':
        eligible_badges_tasker = eligible_badges.filter(
            models.Q(target_role=Badge.TargetRoleChoices.TASKER) |
            models.Q(target_role=Badge.TargetRoleChoices.BOTH)
        )
        for badge in eligible_badges_tasker:
            if _evaluate_badge(badge, profile, user, role='tasker'):
                badges_to_award.append(badge)

    if user.is_client() or user.role == 'both':
        eligible_badges_client = eligible_badges.filter(
            models.Q(target_role=Badge.TargetRoleChoices.CLIENT) |
            models.Q(target_role=Badge.TargetRoleChoices.BOTH)
        )
        for badge in eligible_badges_client:
            if _evaluate_badge(badge, profile, user, role='client'):
                badges_to_award.append(badge)

    for badge in badges_to_award:
        created, _ = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            _notify_badge_earned(user, badge)

    _deduplicate_tasks_completed_badges(user, profile)


def _deduplicate_tasks_completed_badges(user, profile):
    user_badges = UserBadge.objects.filter(
        user=user,
        badge__condition_type=Badge.ConditionTypeChoices.TASKS_COMPLETED,
    ).select_related('badge')

    if user_badges.count() <= 1:
        return

    tiers = []
    for ub in user_badges:
        min_tasks = ub.badge.condition_value.get('min_tasks', 0)
        tiers.append((min_tasks, ub))

    tiers.sort(key=lambda x: x[0], reverse=True)

    best_ub = None
    for min_tasks, ub in tiers:
        if profile.tasks_completed >= min_tasks:
            best_ub = ub
            break

    if best_ub is None:
        user_badges.delete()
        return

    for min_tasks, ub in tiers:
        if ub.id != best_ub.id:
            ub.delete()


def _evaluate_badge(badge, profile, user, role='tasker'):
    """Évalue si un badge doit être attribué en fonction de son type et de ses conditions."""
    already_earned = UserBadge.objects.filter(user=user, badge=badge).exists()
    if already_earned:
        return False

    condition = badge.condition_type
    value = badge.condition_value or {}

    if condition == Badge.ConditionTypeChoices.TASKS_COMPLETED:
        return _check_tasks_completed(value, profile, role)

    elif condition == Badge.ConditionTypeChoices.AVG_RATING:
        return _check_avg_rating(value, profile, role)

    elif condition == Badge.ConditionTypeChoices.NO_CANCEL:
        return _check_no_cancel(value, profile, role)

    elif condition == Badge.ConditionTypeChoices.SPEED:
        return _check_speed(value, user, role)

    elif condition == Badge.ConditionTypeChoices.CUSTOM:
        return _check_custom(value, user, profile, role)

    return False


def _check_tasks_completed(value, profile, role):
    min_tasks = value.get('min_tasks', 0)
    return profile.tasks_completed >= min_tasks


def _check_avg_rating(value, profile, role):
    min_rating = value.get('min_rating', 0)
    min_tasks = value.get('min_tasks', 0)

    if profile.tasks_completed < min_tasks:
        return False

    if role == 'client':
        return profile.client_rating_avg >= min_rating
    return profile.tasker_rating_avg >= min_rating


def _check_no_cancel(value, profile, role):
    max_cancel = value.get('max_cancels', 0)
    min_completed = value.get('min_completed', value.get('min_tasks', 5))
    return profile.tasks_cancelled <= max_cancel and profile.tasks_completed >= min_completed


def _check_speed(value, user, role):
    """Vérifie si le tasker complète les missions rapidement."""
    min_tasks = value.get('min_tasks', 5)
    max_avg_hours = value.get('max_avg_hours', 24)

    if role != 'tasker':
        return False

    completed = Task.objects.filter(
        assigned_tasker=user,
        status__in=[Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED],
    )

    if completed.count() < min_tasks:
        return False

    total_hours = 0
    count = 0
    for task in completed:
        if task.updated_at and task.published_at:
            delta = task.updated_at - task.published_at
            total_hours += delta.total_seconds() / 3600
            count += 1

    if count == 0:
        return False

    avg_hours = total_hours / count
    return avg_hours <= max_avg_hours


def _check_custom(value, user, profile, role):
    """Vérifie des conditions personnalisées définies en JSON."""
    checks = value.get('checks', [])
    if not checks:
        return False

    for check in checks:
        check_type = check.get('type', '')

        if check_type == 'tasks_in_category':
            category_slug = check.get('category_slug')
            min_count = check.get('min_count', 1)

            task_filter = {
                'status__in': [Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED],
            }
            if role == 'tasker':
                task_filter['assigned_tasker'] = user
            elif role == 'client':
                task_filter['client'] = user
            else:
                return False

            if category_slug:
                task_filter['category__slug'] = category_slug
                count = Task.objects.filter(**task_filter).count()
            else:
                qs = Task.objects.filter(**task_filter).exclude(
                    category__isnull=True
                ).values('category').annotate(
                    total=Count('id')
                ).order_by('-total')
                count = qs[0]['total'] if qs else 0

            if count < min_count:
                return False

        elif check_type == 'min_xp':
            if profile.xp < check.get('min_xp', 0):
                return False

        elif check_type == 'min_level':
            if profile.level < check.get('min_level', 1):
                return False

        elif check_type == 'verified':
            if not user.is_verified:
                return False

        elif check_type == 'streak':
            min_streak = check.get('min_streak', 3)
            streak = _calculate_streak(user, role)
            if streak < min_streak:
                return False

        elif check_type == 'review_count':
            min_reviews = check.get('min_reviews', 5)
            if role == 'tasker':
                count = Review.objects.filter(reviewed=user, moderation_status=Review.ModerationStatusChoices.VALIDATED).count()
            else:
                count = Review.objects.filter(reviewer=user, moderation_status=Review.ModerationStatusChoices.VALIDATED).count()
            if count < min_reviews:
                return False

        elif check_type == 'early_adopter':
            days_since_joined = (timezone.now() - user.date_joined).days
            max_days = check.get('max_days', 30)
            if days_since_joined > max_days:
                return False

        elif check_type == 'tasks_published':
            min_count = check.get('min_count', 1)
            count = Task.objects.filter(
                client=user,
                status__in=[Task.StatusChoices.PUBLISHED, Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS, Task.StatusChoices.COMPLETED, Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED, Task.StatusChoices.CLOSED],
            ).count()
            if count < min_count:
                return False

        elif check_type == 'first_task':
            if profile.tasks_completed < 1:
                return False

    return True


def _calculate_streak(user, role='tasker'):
    """Calcule le nombre de jours consécutifs avec au moins une tâche complétée."""
    if role != 'tasker':
        return 0

    tasks = Task.objects.filter(
        assigned_tasker=user,
        status__in=[Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED],
    ).order_by('-updated_at')

    if not tasks.exists():
        return 0

    streak = 0
    current_date = tasks.first().updated_at.date()
    expected_date = current_date

    from datetime import timedelta
    task_dates = set(t.updated_at.date() for t in tasks)

    while current_date in task_dates:
        streak += 1
        current_date -= timedelta(days=1)
        if streak > 365:
            break

    return streak


def _notify_badge_earned(user, badge):
    """Crée une notification quand un badge est gagné."""
    from apps.accounts.models import Notification
    Notification.objects.create(
        user=user,
        type=Notification.TypeChoices.SYSTEM,
        title='Nouveau badge débloqué !',
        message=f'Félicitations ! Vous avez obtenu le badge "{badge.name}".',
    )


def award_xp(user, amount):
    profile = user.profile
    profile.xp += amount
    profile.save(update_fields=['xp', 'updated_at'])
    profile.update_level()


def award_task_completion_bonuses(tasker):
    profile = tasker.profile
    if not profile._xp_awarded_first_task:
        award_xp(tasker, 100)
        profile._xp_awarded_first_task = True
        profile.save(update_fields=['_xp_awarded_first_task', 'updated_at'])
