import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Badge(models.Model):
    class ConditionTypeChoices(models.TextChoices):
        TASKS_COMPLETED = 'tasks_completed', _('Tâches réalisées')
        AVG_RATING = 'avg_rating', _('Note moyenne')
        SPEED = 'speed', _('Rapidité')
        NO_CANCEL = 'no_cancel', _('Aucune annulation')
        CUSTOM = 'custom', _('Personnalisé')

    class TargetRoleChoices(models.TextChoices):
        TASKER = 'tasker', _('Tasker')
        CLIENT = 'client', _('Client')
        BOTH = 'both', _('Les deux')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True, max_length=120)
    description = models.TextField(_('description'))
    icon = models.CharField(_('icône'), max_length=50, default='badge')
    color = models.CharField(_('couleur'), max_length=7, default='#4F46E5')
    condition_type = models.CharField(
        _('type de condition'),
        max_length=20,
        choices=ConditionTypeChoices.choices,
    )
    condition_value = models.JSONField(
        _('valeur de condition'),
        default=dict,
        help_text=_('Ex: {"min_tasks": 10, "min_rating": 4.5}'),
    )
    is_active = models.BooleanField(_('actif'), default=True)
    target_role = models.CharField(
        _('rôle cible'),
        max_length=10,
        choices=TargetRoleChoices.choices,
        default=TargetRoleChoices.BOTH,
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges_earned',
        verbose_name=_('utilisateur'),
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='user_badges',
        verbose_name=_('badge'),
    )
    earned_at = models.DateTimeField(_('obtenu le'), auto_now_add=True)

    class Meta:
        verbose_name = _('badge utilisateur')
        verbose_name_plural = _('badges utilisateur')
        constraints = [
            models.UniqueConstraint(fields=['user', 'badge'], name='unique_user_badge'),
        ]
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.user.full_name} — {self.badge.name}'
