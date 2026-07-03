from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import CustomUser, VerificationRecord, Skill, UserProfile
from apps.badges.engine import check_and_award_badges
from apps.tasks.models import Task

User = get_user_model()


def admin_required(view_func):
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin():
            messages.error(request, _('Accès réservé aux administrateurs.'))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapper


@admin_required
def admin_dashboard(request):
    tasker_ids = User.objects.filter(Q(role='tasker') | Q(role='both')).values_list('id', flat=True)
    profiles_with_skills = UserProfile.objects.filter(user_id__in=tasker_ids, skills__isnull=False).exclude(skills=None).distinct()
    profiles_with_zone = UserProfile.objects.filter(user_id__in=tasker_ids).exclude(city='').exclude(city__isnull=True)
    total_profiles = UserProfile.objects.filter(user_id__in=tasker_ids)

    stats = {
        'total_users': User.objects.count(),
        'clients': User.objects.filter(Q(role='client') | Q(role='both')).count(),
        'taskers': User.objects.filter(Q(role='tasker') | Q(role='both')).count(),
        'pending_verifications': VerificationRecord.objects.filter(
            type=VerificationRecord.TypeChoices.FACE_ID,
            face_status=VerificationRecord.FaceStatusChoices.PENDING,
        ).count(),
        'active_missions': Task.objects.filter(status__in=['published', 'accepted', 'in_progress', 'awaiting_confirmation']).count(),
        'open_litiges': Task.objects.filter(status='litige').count(),
        'total_tasks': Task.objects.count(),
        'taskers_with_skills': profiles_with_skills.count(),
        'taskers_with_zone': profiles_with_zone.count(),
        'total_taskers': total_profiles.count(),
    }

    top_skills = Skill.objects.annotate(
        user_count=Count('userprofile')
    ).filter(user_count__gt=0).order_by('-user_count')[:10]

    top_cities = UserProfile.objects.filter(
        user_id__in=tasker_ids
    ).exclude(city='').exclude(city__isnull=True).values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    recent_users = User.objects.filter(is_staff=False).order_by('-date_joined')[:10]
    recent_verifications = VerificationRecord.objects.filter(
        type=VerificationRecord.TypeChoices.FACE_ID,
    ).select_related('user').order_by('-created_at')[:10]
    litiges = Task.objects.filter(status='litige').select_related('client', 'assigned_tasker').order_by('-updated_at')[:5]

    return render(request, 'admin_KaynBricool/dashboard.html', {
        'stats': stats,
        'top_skills': top_skills,
        'top_cities': top_cities,
        'recent_users': recent_users,
        'recent_verifications': recent_verifications,
        'litiges': litiges,
    })


@admin_required
def admin_users(request):
    search = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.filter(is_staff=False).select_related('profile').prefetch_related('profile__skills').order_by('-date_joined')

    if search:
        users = users.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'admin_KaynBricool/users.html', {
        'users': users,
        'search': search,
        'role_filter': role_filter,
    })


@admin_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
    profile = getattr(user, 'profile', None)
    return render(request, 'admin_KaynBricool/user_detail.html', {
        'profile_user': user,
        'profile': profile,
    })


@admin_required
def admin_ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, _('Utilisateur {} banni.').format(user.full_name))
        return redirect('admin_KaynBricool:users')
    return render(request, 'admin_KaynBricool/user_confirm_ban.html', {'profile_user': user})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
    if request.method == 'POST':
        user.delete()
        messages.success(request, _('Utilisateur {} supprimé.').format(user.full_name))
        return redirect('admin_KaynBricool:users')
    return render(request, 'admin_KaynBricool/user_confirm_delete.html', {'profile_user': user})


@admin_required
def admin_verifications(request):
    status_filter = request.GET.get('status', 'pending')

    verifications = VerificationRecord.objects.filter(
        type=VerificationRecord.TypeChoices.FACE_ID,
    ).select_related('user').order_by('-created_at')

    if status_filter == 'pending':
        verifications = verifications.filter(face_status=VerificationRecord.FaceStatusChoices.PENDING)
    elif status_filter == 'approved':
        verifications = verifications.filter(face_status=VerificationRecord.FaceStatusChoices.APPROVED)
    elif status_filter == 'rejected':
        verifications = verifications.filter(face_status=VerificationRecord.FaceStatusChoices.REJECTED)
    elif status_filter == 'all':
        pass

    return render(request, 'admin_KaynBricool/verifications.html', {
        'verifications': verifications,
        'status_filter': status_filter,
    })


@admin_required
def admin_verify_face(request, verification_id):
    verification = get_object_or_404(VerificationRecord, id=verification_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        verification.admin_notes = notes

        if action == 'approve':
            verification.face_status = VerificationRecord.FaceStatusChoices.APPROVED
            verification.save(update_fields=['face_status', 'admin_notes', 'updated_at'])
            verification.user.is_verified = True
            verification.user.save(update_fields=['is_verified', 'updated_at'])
            verification.user.profile.award_profile_xp()
            check_and_award_badges(verification.user)
            messages.success(request, _('Vérification de {} approuvée.').format(verification.user.full_name))
        elif action == 'reject':
            verification.face_status = VerificationRecord.FaceStatusChoices.REJECTED
            verification.save(update_fields=['face_status', 'admin_notes', 'updated_at'])
            messages.warning(request, _('Vérification de {} rejetée.').format(verification.user.full_name))

        return redirect('admin_KaynBricool:verifications')

    return render(request, 'admin_KaynBricool/verify_face.html', {
        'verification': verification,
    })


@admin_required
def admin_delete_face_photo(request, verification_id, photo_name):
    verification = get_object_or_404(VerificationRecord, id=verification_id)
    valid_photos = ['face_photo_initial', 'face_photo_left', 'face_photo_right', 'face_photo_blink']

    if photo_name not in valid_photos:
        messages.error(request, _('Photo invalide.'))
        return redirect('admin_KaynBricool:verify_face', verification_id=verification.id)

    photo_field = getattr(verification, photo_name)
    if photo_field:
        photo_field.delete(save=False)
        setattr(verification, photo_name, None)
        verification.save(update_fields=[photo_name, 'updated_at'])
        messages.success(request, _('Photo supprimée.'))
    else:
        messages.info(request, _('Cette photo n\'existe pas.'))

    return redirect('admin_KaynBricool:verify_face', verification_id=verification.id)


@admin_required
def admin_delete_verification(request, verification_id):
    verification = get_object_or_404(VerificationRecord, id=verification_id)
    user_name = verification.user.full_name
    verification.delete()
    messages.success(request, _('Vérification Face ID de {} supprimée.').format(user_name))
    return redirect('admin_KaynBricool:verifications')
