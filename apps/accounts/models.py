import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.accounts.managers import CustomUserManager


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email'), unique=True)

    class Roles(models.TextChoices):
        CLIENT = 'client', _('Client')
        TASKER = 'tasker', _('Tasker')
        BOTH = 'both', _('Client & Tasker')
        ADMIN = 'admin', _('Admin')

    class ActiveRoles(models.TextChoices):
        CLIENT = 'client', _('Client')
        TASKER = 'tasker', _('Tasker')
        ADMIN = 'admin', _('Admin')

    full_name = models.CharField(_('nom complet'), max_length=200)
    phone_number = models.CharField(_('téléphone'), max_length=20, blank=True, null=True)
    phone_verified = models.BooleanField(_('téléphone vérifié'), default=False)
    email_verified = models.BooleanField(_('email vérifié'), default=False)
    avatar = models.ImageField(
        _('photo de profil'),
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    role = models.CharField(
        _('rôle'),
        max_length=10,
        choices=Roles.choices,
        default=Roles.CLIENT,
    )
    active_role = models.CharField(
        _('rôle actif'),
        max_length=10,
        choices=ActiveRoles.choices,
        default=ActiveRoles.CLIENT,
    )
    is_verified = models.BooleanField(_('vérifié'), default=False)
    firebase_uid = models.CharField(_('UID Firebase'), max_length=128, blank=True, null=True, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def can_switch_role(self):
        return self.role == self.Roles.BOTH

    def switch_role(self):
        if self.can_switch_role:
            if self.active_role == self.ActiveRoles.CLIENT:
                self.active_role = self.ActiveRoles.TASKER
            else:
                self.active_role = self.ActiveRoles.CLIENT
            self.save(update_fields=['active_role'])

    def is_client(self):
        return self.role in (self.Roles.CLIENT, self.Roles.BOTH)

    def is_tasker(self):
        return self.role in (self.Roles.TASKER, self.Roles.BOTH)

    def acting_as_client(self):
        return self.active_role == self.ActiveRoles.CLIENT

    def acting_as_tasker(self):
        return self.active_role == self.ActiveRoles.TASKER

    def is_admin(self):
        return self.role == self.Roles.ADMIN


class VerificationRecord(models.Model):
    class TypeChoices(models.TextChoices):
        PHONE = 'phone', _('Téléphone')
        EMAIL = 'email', _('Email')
        FACE_ID = 'face_id', _('Face ID')

    class FaceStatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        APPROVED = 'approved', _('Approuvé')
        REJECTED = 'rejected', _('Rejeté')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name=_('utilisateur'),
    )
    type = models.CharField(
        _('type'),
        max_length=10,
        choices=TypeChoices.choices,
    )
    code = models.CharField(_('code'), max_length=6, blank=True, null=True)
    expires_at = models.DateTimeField(_('expire le'))
    is_used = models.BooleanField(_('utilisé'), default=False)

    face_photo_initial = models.ImageField(
        _('photo initiale'),
        upload_to='face-id/',
        blank=True,
        null=True,
    )
    face_photo_left = models.ImageField(
        _('photo gauche'),
        upload_to='face-id/',
        blank=True,
        null=True,
    )
    face_photo_right = models.ImageField(
        _('photo droite'),
        upload_to='face-id/',
        blank=True,
        null=True,
    )
    face_photo_blink = models.ImageField(
        _('photo clignement'),
        upload_to='face-id/',
        blank=True,
        null=True,
    )
    face_status = models.CharField(
        _('statut face ID'),
        max_length=10,
        choices=FaceStatusChoices.choices,
        default=FaceStatusChoices.PENDING,
    )
    admin_notes = models.TextField(_('notes admin'), blank=True, null=True)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('vérification')
        verbose_name_plural = _('vérifications')
        constraints = [
            models.UniqueConstraint(fields=['user', 'type'], name='unique_user_verification_type'),
        ]

    def __str__(self):
        return f'{self.user.full_name} - {self.get_type_display()}'


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('utilisateur'),
    )
    bio = models.TextField(_('biographie'), blank=True, null=True)
    city = models.CharField(_('ville'), max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )

    tasker_rating_avg = models.DecimalField(
        _('note tasker moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    tasker_rating_count = models.IntegerField(_('nombre avis tasker'), default=0)
    client_rating_avg = models.DecimalField(
        _('note client moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    client_rating_count = models.IntegerField(_('nombre avis client'), default=0)

    tasks_completed = models.IntegerField(_('tâches réalisées'), default=0)
    tasks_published = models.IntegerField(_('tâches publiées'), default=0)
    tasks_cancelled = models.IntegerField(_('tâches annulées'), default=0)

    xp = models.IntegerField(_('points d\'expérience'), default=0)
    level = models.IntegerField(_('niveau'), default=1)

    onboarding_seen = models.BooleanField(_('guide vu'), default=False)
    current_streak = models.IntegerField(_('série actuelle'), default=0)
    last_streak_date = models.DateField(_('dernière activité'), blank=True, null=True)
    saved_tasks = models.ManyToManyField('tasks.Task', blank=True, related_name='saved_by')

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    def update_streak(self):
        from datetime import date, timedelta
        today = date.today()
        if self.last_streak_date == today:
            return
        if self.last_streak_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.last_streak_date = today
        self.save(update_fields=['current_streak', 'last_streak_date', 'updated_at'])

    class Meta:
        verbose_name = _('profil')
        verbose_name_plural = _('profils')

    def __str__(self):
        return f'Profil de {self.user.full_name}'


class Notification(models.Model):
    class TypeChoices(models.TextChoices):
        TASK_PUBLISHED = 'task_published', _('Nouvelle tâche publiée')
        NEW_APPLICATION = 'new_application', _('Nouvelle candidature')
        TASK_ACCEPTED = 'task_accepted', _('Tâche acceptée')
        TASK_COMPLETED = 'task_completed', _('Tâche terminée')
        MESSAGE_RECEIVED = 'message_received', _('Nouveau message')
        REVIEW_RECEIVED = 'review_received', _('Nouvel avis')
        SYSTEM = 'system', _('Système')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('utilisateur'),
    )
    type = models.CharField(
        _('type'),
        max_length=30,
        choices=TypeChoices.choices,
    )
    title = models.CharField(_('titre'), max_length=200)
    message = models.TextField(_('message'))
    is_read = models.BooleanField(_('lue'), default=False)
    is_opened = models.BooleanField(_('ouverte'), default=False)
    related_task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('tâche liée'),
    )
    related_conversation = models.ForeignKey(
        'messaging.Conversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('conversation liée'),
    )
    related_review = models.ForeignKey(
        'reputation.Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('avis lié'),
    )
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    read_at = models.DateTimeField(_('lue le'), blank=True, null=True)
    opened_at = models.DateTimeField(_('ouverte le'), blank=True, null=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.full_name} — {self.title}'

    def mark_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def mark_opened(self):
        from django.utils import timezone
        self.is_opened = True
        self.opened_at = timezone.now()
        self.save(update_fields=['is_opened', 'opened_at'])
