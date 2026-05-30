import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        'tasks.TaskApplication',
        on_delete=models.CASCADE,
        related_name='conversation',
        verbose_name=_('candidature'),
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_conversations',
        verbose_name=_('client'),
    )
    tasker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasker_conversations',
        verbose_name=_('tasker'),
    )
    is_reported = models.BooleanField(_('signalée'), default=False)
    is_closed = models.BooleanField(_('clôturée'), default=False)
    report_reason = models.TextField(_('raison du signalement'), blank=True, null=True)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    last_activity_at = models.DateTimeField(_('dernière activité'), auto_now=True)

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-last_activity_at']

    def __str__(self):
        return f'{self.application.task.title} — {self.client.full_name} / {self.tasker.full_name}'

    @property
    def task(self):
        return self.application.task

    def participants(self):
        return [self.client, self.tasker]

    def other_participant(self, user):
        if user == self.client:
            return self.tasker
        return self.client

    def close(self):
        self.is_closed = True
        self.save(update_fields=['is_closed', 'last_activity_at'])

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation'),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('expéditeur'),
    )
    content = models.TextField(_('message'), max_length=5000)
    is_read = models.BooleanField(_('lu'), default=False)
    created_at = models.DateTimeField(_('envoyé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender.full_name}: {self.content[:50]}...'
