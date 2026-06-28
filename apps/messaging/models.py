import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    report_reason = models.TextField(_('raison du signalement'), blank=True, null=True)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    last_activity_at = models.DateTimeField(_('dernière activité'), auto_now=True)

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-last_activity_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'tasker'], name='unique_client_tasker_pair'),
        ]

    def __str__(self):
        return f'{self.client.full_name} / {self.tasker.full_name}'

    def participants(self):
        return [self.client, self.tasker]

    def other_participant(self, user):
        if user == self.client:
            return self.tasker
        return self.client

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
        null=True, blank=True,
        verbose_name=_('expéditeur'),
    )
    content = models.TextField(_('message'), max_length=5000, blank=True, default='')
    file = models.FileField(_('fichier'), upload_to='chat_files/', blank=True, null=True)
    file_name = models.CharField(_('nom du fichier'), max_length=255, blank=True, default='')
    is_system = models.BooleanField(_('message système'), default=False)
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
        sender_name = self.sender.full_name if self.sender else 'Système'
        return f'{sender_name}: {self.content[:50]}...'
