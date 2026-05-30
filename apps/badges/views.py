from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.badges.models import Badge, UserBadge
from apps.accounts.models import CustomUser


def badge_list(request):
    badges = Badge.objects.filter(is_active=True)
    return render(request, 'badges/badge_list.html', {'badges': badges})


def badge_detail(request, badge_slug):
    badge = get_object_or_404(Badge, slug=badge_slug)
    return render(request, 'badges/badge_detail.html', {'badge': badge})


@login_required
def my_badges(request):
    role = request.GET.get('role', '')
    if role == 'tasker':
        user_badges = UserBadge.objects.filter(
            user=request.user,
            badge__target_role__in=['tasker', 'both'],
        ).select_related('badge').order_by('-earned_at')
    elif role == 'client':
        user_badges = UserBadge.objects.filter(
            user=request.user,
            badge__target_role__in=['client', 'both'],
        ).select_related('badge').order_by('-earned_at')
    else:
        user_badges = UserBadge.objects.filter(user=request.user).select_related('badge').order_by('-earned_at')

    all_client = UserBadge.objects.filter(
        user=request.user,
        badge__target_role__in=['client', 'both'],
    ).count()
    all_tasker = UserBadge.objects.filter(
        user=request.user,
        badge__target_role__in=['tasker', 'both'],
    ).count()

    return render(request, 'badges/my_badges.html', {
        'user_badges': user_badges,
        'active_role': role,
        'client_count': all_client,
        'tasker_count': all_tasker,
    })
