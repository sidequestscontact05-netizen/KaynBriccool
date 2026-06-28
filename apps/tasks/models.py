import uuid
import logging
from datetime import timedelta
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True, max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True, default='folder')
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['name']

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name=_('catégorie'),
    )
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    is_active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('sous-catégorie')
        verbose_name_plural = _('sous-catégories')
        constraints = [
            models.UniqueConstraint(fields=['category', 'slug'], name='unique_category_subcategory_slug'),
        ]
        ordering = ['name']

    def __str__(self):
        return f'{self.category.name} > {self.name}'


class Task(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', _('Brouillon')
        PUBLISHED = 'published', _('Publiée')
        ACCEPTED = 'accepted', _('Acceptée')
        IN_PROGRESS = 'in_progress', _('En cours')
        COMPLETED = 'completed', _('Terminée')
        AWAITING_CONFIRMATION = 'awaiting_confirmation', _('En attente de confirmation')
        VALIDATED = 'validated', _('Validée')
        LITIGE = 'litige', _('Litige')
        RESOLVED = 'resolved', _('Résolue')
        EVALUATED = 'evaluated', _('Évaluée')
        CLOSED = 'closed', _('Clôturée')
        CANCELLED = 'cancelled', _('Annulée')
        REJECTED = 'rejected', _('Refusée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='published_tasks',
        verbose_name=_('client'),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('catégorie'),
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('sous-catégorie'),
    )
    title = models.CharField(_('titre'), max_length=200, blank=True, default='')
    description = models.TextField(_('description'), blank=True, default='')
    reward = models.DecimalField(
        _('rémunération'),
        max_digits=8,
        decimal_places=2,
    )
    status = models.CharField(
        _('statut'),
        max_length=30,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )

    has_route = models.BooleanField(_('avec trajet'), default=False)
    proof_required = models.BooleanField(_('preuve requise'), default=False)
    departure_lat = models.FloatField(_('lat départ'), blank=True, null=True)
    departure_lng = models.FloatField(_('lng départ'), blank=True, null=True)
    arrival_lat = models.FloatField(_('lat arrivée'), blank=True, null=True)
    arrival_lng = models.FloatField(_('lng arrivée'), blank=True, null=True)
    departure_address = models.CharField(_('adresse de départ'), max_length=300, blank=True, null=True)
    arrival_address = models.CharField(_('adresse d\'arrivée'), max_length=300, blank=True, default='')

    assigned_tasker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_tasks',
        verbose_name=_('tasker assigné'),
    )

    photos = models.JSONField(_('photos'), default=list, blank=True)
    files = models.JSONField(_('fichiers'), default=list, blank=True)

    published_at = models.DateTimeField(_('publiée le'), blank=True, null=True)
    def _default_deadline():
        return timezone.now() + timedelta(days=7)

    deadline = models.DateTimeField(
        _('date limite'),
        default=_default_deadline,
        help_text="Délai par défaut : 7 jours",
        blank=True,
        null=True,
    )
    closed_at = models.DateTimeField(_('clôturée le'), blank=True, null=True)

    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifiée le'), auto_now=True)

    class Meta:
        verbose_name = _('tâche')
        verbose_name_plural = _('tâches')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def accept_tasker(self, tasker):
        with transaction.atomic():
            task = Task.objects.select_for_update().get(pk=self.pk)
            if task.status != self.StatusChoices.PUBLISHED:
                raise ValidationError("La mission n'est pas disponible ou déjà acceptée")
            task.status = self.StatusChoices.ACCEPTED
            task.assigned_tasker = tasker
            task.save()
            for app in task.applications.exclude(tasker=tasker):
                app.reject()

    def notify_client_new_application(self, application):
        subject = f"Nouvelle candidature pour {self.title}"
        message = (
            f"Bonjour,\n\n"
            f"{application.tasker.full_name} a postulé à votre mission "
            f"'{self.title}'.\n\n"
            f"Connectez-vous pour voir les candidatures."
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.client.email],
            fail_silently=True,
        )

    def start(self):
        if self.status == self.StatusChoices.ACCEPTED:
            self.status = self.StatusChoices.IN_PROGRESS
            self.save(update_fields=['status', 'updated_at'])

    def await_confirmation(self):
        if self.status in (self.StatusChoices.IN_PROGRESS, self.StatusChoices.AWAITING_CONFIRMATION):
            self.status = self.StatusChoices.AWAITING_CONFIRMATION
            self.save(update_fields=['status', 'updated_at'])

    def validate(self):
        if self.status == self.StatusChoices.AWAITING_CONFIRMATION:
            self.status = self.StatusChoices.VALIDATED
            self.save(update_fields=['status', 'updated_at'])

    def open_litige(self, reason=''):
        if self.status in (self.StatusChoices.IN_PROGRESS, self.StatusChoices.AWAITING_CONFIRMATION):
            self.status = self.StatusChoices.LITIGE
            self.save(update_fields=['status', 'updated_at'])

    def resolve_litige(self):
        if self.status == self.StatusChoices.LITIGE:
            self.status = self.StatusChoices.RESOLVED
            self.save(update_fields=['status', 'updated_at'])

    def evaluate(self):
        if self.status in (self.StatusChoices.VALIDATED, self.StatusChoices.RESOLVED):
            self.status = self.StatusChoices.EVALUATED
            self.save(update_fields=['status', 'updated_at'])

    def close(self):
        self.status = self.StatusChoices.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

    def reject(self):
        if self.status == self.StatusChoices.AWAITING_CONFIRMATION:
            self.status = self.StatusChoices.REJECTED
            self.save(update_fields=['status', 'updated_at'])

    @property
    def is_expired(self):
        if self.deadline and self.status in (
            self.StatusChoices.PUBLISHED,
            self.StatusChoices.ACCEPTED,
            self.StatusChoices.IN_PROGRESS,
        ):
            return timezone.now() > self.deadline
        return False


class TaskApplication(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        ACCEPTED = 'accepted', _('Acceptée')
        REJECTED = 'rejected', _('Rejetée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('tâche'),
    )
    tasker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_applications',
        verbose_name=_('tasker'),
    )
    message = models.TextField(_('message du tasker'), blank=True, null=True)
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    created_at = models.DateTimeField(_('postulé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('candidature')
        verbose_name_plural = _('candidatures')
        constraints = [
            models.UniqueConstraint(fields=['task', 'tasker'], name='unique_task_tasker_application'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tasker.full_name} → {self.task.title}'

    def accept(self):
        self.status = self.StatusChoices.ACCEPTED
        self.save(update_fields=['status', 'updated_at'])

    def reject(self):
        self.status = self.StatusChoices.REJECTED
        self.save(update_fields=['status', 'updated_at'])


class TaskProof(models.Model):
    class ReviewChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        ACCEPTED = 'accepted', _('Acceptée')
        REVISION_REQUESTED = 'revision', _('Modification demandée')
        REJECTED = 'rejected', _('Refusée')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name='proof',
        verbose_name=_('tâche'),
    )
    tasker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('tasker'),
    )
    description = models.TextField(_('description de la preuve'))
    photos = models.JSONField(_('photos'), default=list, blank=True)
    submitted_at = models.DateTimeField(_('soumise le'), auto_now_add=True)

    client_review = models.CharField(
        _('révision client'),
        max_length=20,
        choices=ReviewChoices.choices,
        default=ReviewChoices.PENDING,
    )
    revision_notes = models.TextField(
        _('notes de révision'),
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(_('révisée le'), blank=True, null=True)

    class Meta:
        verbose_name = _('preuve')
        verbose_name_plural = _('preuves')

    def __str__(self):
        return f'Preuve pour {self.task.title}'

    def request_revision(self, notes):
        self.client_review = self.ReviewChoices.REVISION_REQUESTED
        self.revision_notes = notes
        self.reviewed_at = timezone.now()
        self.save(update_fields=['client_review', 'revision_notes', 'reviewed_at'])

    def accept(self):
        self.client_review = self.ReviewChoices.ACCEPTED
        self.reviewed_at = timezone.now()
        self.save(update_fields=['client_review', 'reviewed_at'])
