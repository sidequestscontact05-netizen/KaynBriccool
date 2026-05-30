from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, JsonResponse

from apps.accounts.models import CustomUser, UserProfile, VerificationRecord
from apps.accounts.forms import (
    ClientRegistrationForm,
    TaskerRegistrationForm,
    CustomLoginForm,
    PhoneVerificationForm,
    FaceIdVerificationForm,
    ProfileUpdateForm,
    CustomPasswordResetForm,
)
from apps.accounts.utils import (
    create_phone_verification,
    verify_phone_code,
    send_password_reset_email,
    create_email_verification,
    verify_email_code,
    send_form_email,
)
from apps.reputation.models import Review
from apps.badges.models import UserBadge


def register_choice(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'accounts/register_choice.html')


class ClientRegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = ClientRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            create_email_verification(user)
            send_form_email(user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        return render(request, self.template_name, {'form': form})


class TaskerRegisterView(View):
    template_name = 'accounts/register_tasker.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = TaskerRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = TaskerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            base64_fields = [
                'face_photo_initial_data',
                'face_photo_left_data',
                'face_photo_right_data',
                'face_photo_blink_data',
            ]
            face_data = [request.POST.get(f, '') for f in base64_fields]

            if not all(face_data):
                messages.error(request, _('Vérification faciale incomplète. Reprenez les 4 photos.'))
                return render(request, self.template_name, {'form': form})

            import base64
            from django.core.files.base import ContentFile
            from django.utils import timezone
            from datetime import timedelta

            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            create_email_verification(user)
            send_form_email(user)

            verification = VerificationRecord.objects.create(
                user=user,
                type=VerificationRecord.TypeChoices.FACE_ID,
                face_status=VerificationRecord.FaceStatusChoices.PENDING,
                expires_at=timezone.now() + timedelta(days=365),
            )

            photo_names = ['face_photo_initial', 'face_photo_left', 'face_photo_right', 'face_photo_blink']
            for i, data in enumerate(face_data):
                if ',' in data:
                    data = data.split(',')[1]
                img_bytes = base64.b64decode(data)
                getattr(verification, photo_names[i]).save(photo_names[i] + '.jpg', ContentFile(img_bytes), save=False)
            verification.save()

            messages.success(request, _('Compte tasker créé !'))
            return redirect('home')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('home')


class VerifyPhoneView(LoginRequiredMixin, View):
    template_name = 'accounts/verify_phone.html'

    def get(self, request):
        form = PhoneVerificationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if verify_phone_code(request.user, code):
                messages.success(request, _('Numéro vérifié avec succès !'))
                if request.user.acting_as_tasker():
                    return redirect('tasks:tasker_dashboard')
                return redirect('tasks:client_dashboard')
            else:
                messages.error(request, _('Code invalide ou expiré.'))
        return render(request, self.template_name, {'form': form})


class ResendCodeView(LoginRequiredMixin, View):
    def post(self, request):
        create_phone_verification(request.user)
        messages.info(request, _('Nouveau code envoyé par email.'))
        return redirect('accounts:verify_phone')


@method_decorator(ensure_csrf_cookie, name='get')
class VerifyEmailView(LoginRequiredMixin, View):
    template_name = 'accounts/verify_email.html'

    def get(self, request):
        if request.user.email_verified:
            return redirect('home')
        return render(request, self.template_name)

    def post(self, request):
        code = request.POST.get('code', '').strip()
        if not code:
            messages.error(request, _('Entrez le code de vérification.'))
            return render(request, self.template_name)

        if verify_email_code(request.user, code):
            messages.success(request, _('Email vérifié avec succès !'))
            if request.user.acting_as_tasker():
                return redirect('tasks:tasker_dashboard')
            return redirect('tasks:client_dashboard')
        else:
            messages.error(request, _('Code invalide ou expiré.'))
            return render(request, self.template_name, {'error': True})


class ResendEmailCodeView(LoginRequiredMixin, View):
    def post(self, request):
        create_email_verification(request.user)
        messages.info(request, _('Nouveau code envoyé à votre email.'))
        return redirect('accounts:verify_email')


class VerifyFaceIdView(LoginRequiredMixin, View):
    template_name = 'accounts/verify_face.html'

    def get(self, request):
        if request.user.role != CustomUser.Roles.TASKER and request.user.role != CustomUser.Roles.BOTH:
            return HttpResponseForbidden(_('Réservé aux taskers.'))

        form = FaceIdVerificationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FaceIdVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = VerificationRecord.objects.create(
                user=request.user,
                type=VerificationRecord.TypeChoices.FACE_ID,
                face_status=VerificationRecord.FaceStatusChoices.PENDING,
            )
            form.save_m2m() if hasattr(form, 'save_m2m') else None

            verification.face_photo_initial = request.FILES.get('face_photo_initial')
            verification.face_photo_left = request.FILES.get('face_photo_left')
            verification.face_photo_right = request.FILES.get('face_photo_right')
            verification.face_photo_blink = request.FILES.get('face_photo_blink')
            verification.save()

            messages.success(request, _('Photos envoyées. En attente de validation par l\'admin.'))
            return redirect('tasks:tasker_dashboard')

        return render(request, self.template_name, {'form': form})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        users = CustomUser.objects.filter(email__iexact=email)
        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            send_password_reset_email(user, reset_url)
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def get_success_url(self):
        messages.success(self.request, _('Votre mot de passe a été modifié. Vous pouvez maintenant vous connecter.'))
        return super().get_success_url()
    
    def form_valid(self, form):
        user = form.user
        if user:
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
            self.request.session['password_just_reset'] = True
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        return context


@login_required
def switch_role(request):
    user = request.user
    if user.can_switch_role:
        user.switch_role()
        messages.info(
            request,
            _('Mode changé : ') + (
                _('Client') if user.acting_as_client() else _('Tasker')
            )
        )
        if user.acting_as_tasker():
            return redirect('tasks:tasker_dashboard')
        return redirect('tasks:client_dashboard')
    return redirect('home')


@login_required
def become_tasker(request):
    user = request.user
    if not user.is_client() or user.role == 'both' or user.is_tasker():
        return redirect('home')

    if request.method == 'POST':
        face_data_fields = [
            'face_photo_initial_data',
            'face_photo_left_data',
            'face_photo_right_data',
            'face_photo_blink_data',
        ]
        face_data = [request.POST.get(f, '') for f in face_data_fields]

        if not all(face_data):
            messages.error(request, _('Vérification faciale incomplète. Reprenez les 4 photos.'))
            return render(request, 'accounts/become_tasker.html')

        import base64
        from django.core.files.base import ContentFile
        from django.utils import timezone
        from datetime import timedelta

        verification = VerificationRecord.objects.create(
            user=user,
            type=VerificationRecord.TypeChoices.FACE_ID,
            face_status=VerificationRecord.FaceStatusChoices.PENDING,
            expires_at=timezone.now() + timedelta(days=365),
        )

        photo_names = ['face_photo_initial', 'face_photo_left', 'face_photo_right', 'face_photo_blink']
        for i, data in enumerate(face_data):
            if ',' in data:
                data = data.split(',')[1]
            img_bytes = base64.b64decode(data)
            getattr(verification, photo_names[i]).save(photo_names[i] + '.jpg', ContentFile(img_bytes), save=False)
        verification.save()

        user.role = CustomUser.Roles.BOTH
        user.active_role = CustomUser.ActiveRoles.TASKER
        user.save(update_fields=['role', 'active_role'])

        messages.success(request, _('Vérification envoyée ! Vous avez maintenant accès à l\'espace Tasker.'))
        return redirect('tasks:tasker_dashboard')

    return render(request, 'accounts/become_tasker.html')


@login_required
def become_client(request):
    user = request.user
    if not user.is_tasker():
        return redirect('home')

    if user.role == CustomUser.Roles.TASKER:
        user.role = CustomUser.Roles.BOTH
        user.active_role = CustomUser.ActiveRoles.CLIENT
        user.save(update_fields=['role', 'active_role'])
        messages.success(request, _('Vous êtes maintenant aussi Client. Vous pouvez créer des tâches !'))
    else:
        user.active_role = CustomUser.ActiveRoles.CLIENT
        user.save(update_fields=['active_role'])
        messages.info(request, _('Mode Client activé.'))

    return redirect('tasks:client_dashboard')


def custom_logout(request):
    logout(request)
    return redirect('home')


def tasker_profile(request, tasker_id):
    tasker = get_object_or_404(CustomUser, id=tasker_id, is_staff=False)
    if not (tasker.role in (CustomUser.Roles.TASKER, CustomUser.Roles.BOTH)):
        messages.error(request, _('Ce profil n\'est pas un tasker.'))
        return redirect('home')

    profile = tasker.profile
    reviews = Review.objects.filter(
        reviewed=tasker,
        review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
        moderation_status=Review.ModerationStatusChoices.VALIDATED,
    ).order_by('-created_at')[:10]

    badges = UserBadge.objects.filter(
        user=tasker,
        badge__is_active=True,
    ).select_related('badge').order_by('badge__name')

    context = {
        'tasker': tasker,
        'profile': profile,
        'reviews': reviews,
        'badges': badges,
        'total_reviews': reviews.count(),
    }
    return render(request, 'accounts/tasker_profile.html', context)


@login_required
def social_complete(request):
    if request.method == 'POST':
        role = request.POST.get('role', 'client')
        user = request.user
        if role == 'tasker':
            user.role = CustomUser.Roles.TASKER
            user.active_role = CustomUser.ActiveRoles.TASKER
        else:
            user.role = CustomUser.Roles.CLIENT
            user.active_role = CustomUser.ActiveRoles.CLIENT
        user.save(update_fields=['role', 'active_role'])

        face_data = request.POST.get('face_photo_data', '')
        if face_data and role == 'tasker':
            import base64
            from django.core.files.base import ContentFile
            from django.utils import timezone
            from datetime import timedelta

            verification = VerificationRecord.objects.create(
                user=user,
                type=VerificationRecord.TypeChoices.FACE_ID,
                face_status=VerificationRecord.FaceStatusChoices.PENDING,
                expires_at=timezone.now() + timedelta(days=365),
            )
            if ',' in face_data:
                face_data = face_data.split(',')[1]
            img_bytes = base64.b64decode(face_data)
            verification.face_photo_initial.save('face_initial.jpg', ContentFile(img_bytes), save=True)

        return redirect('home')

    return render(request, 'accounts/social_complete.html')


@login_required
def onboarding_done(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.onboarding_seen = True
        profile.save(update_fields=['onboarding_seen'])
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'POST only'}, status=405)
