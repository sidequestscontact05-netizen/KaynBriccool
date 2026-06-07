import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Review(models.Model):
    class ReviewTypeChoices(models.TextChoices):
        CLIENT_REVIEWS_TASKER = 'client_to_tasker', _('Client → Tasker')
        TASKER_REVIEWS_CLIENT = 'tasker_to_client', _('Tasker → Client')

    class ModerationStatusChoices(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        VALIDATED = 'validated', _('Validée')
        REPORTED = 'reported', _('Signalée')
        HIDDEN = 'hidden', _('Masquée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('task'),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name=_('évaluateur'),
    )
    reviewed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name=_('évalué'),
    )
    rating = models.IntegerField(
        _('note'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True,
    )
    comment = models.TextField(
        _('commentaire'),
        max_length=1000,
        blank=True,
        null=True,
    )
    review_type = models.CharField(
        _('type'),
        max_length=20,
        choices=ReviewTypeChoices.choices,
    )
    moderation_status = models.CharField(
        _('statut de modération'),
        max_length=20,
        choices=ModerationStatusChoices.choices,
        default=ModerationStatusChoices.DRAFT,
    )
    report_reason = models.TextField(
        _('raison du signalement'),
        blank=True,
        null=True,
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_made',
        verbose_name=_('signalé par'),
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('avis')
        verbose_name_plural = _('avis')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['task', 'reviewer'], name='unique_task_reviewer_review'),
        ]

    def __str__(self):
        return f'{self.reviewer.full_name} → {self.reviewed.full_name} ({self.rating}/5)'

    def report(self, reason, reported_by):
        self.moderation_status = self.ModerationStatusChoices.REPORTED
        self.report_reason = reason
        self.reported_by = reported_by
        self.save(update_fields=['moderation_status', 'report_reason', 'reported_by', 'updated_at'])


