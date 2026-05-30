import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseForbidden
from apps.badges.models import Badge


def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_required
@ensure_csrf_cookie
def admin_badges(request):
    badges = Badge.objects.all().order_by('name')
    return render(request, 'admin_sidequest/badges.html', {
        'badges': badges,
    })


@admin_required
@ensure_csrf_cookie
def admin_create_badge(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or name.lower().replace(' ', '-')
        condition_type = request.POST.get('condition_type', 'tasks_completed')
        value = request.POST.get('condition_value')

        if not name:
            messages.error(request, _('Le nom est obligatoire.'))
            return render(request, 'admin_sidequest/badge_form.html', {'form_action': 'create'})

        try:
            cond_value = json.loads(value) if value else {"min_tasks": 10}
        except json.JSONDecodeError:
            messages.error(request, _('JSON invalide pour la condition.'))
            return render(request, 'admin_sidequest/badge_form.html', {'form_action': 'create'})

        try:
            Badge.objects.create(
                name=name,
                slug=slug,
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', 'badge'),
                color=request.POST.get('color', '#4F46E5'),
                condition_type=condition_type,
                condition_value=cond_value,
                is_active=request.POST.get('is_active') == 'on',
                target_role=request.POST.get('target_role', 'tasker'),
            )
            messages.success(request, _('Badge créé.'))
            return redirect('admin_sidequest:badges')
        except Exception as e:
            messages.error(request, f'Erreur: {e}')
    return render(request, 'admin_sidequest/badge_form.html', {'form_action': 'create'})


@admin_required
@ensure_csrf_cookie
def admin_edit_badge(request, badge_id):
    badge = get_object_or_404(Badge, id=badge_id)
    if request.method == 'POST':
        badge.name = request.POST.get('name', '').strip()
        new_slug = request.POST.get('slug', '').strip()
        badge.condition_type = request.POST.get('condition_type', badge.condition_type)
        badge.is_active = request.POST.get('is_active') == 'on'
        badge.target_role = request.POST.get('target_role', badge.target_role)
        badge.description = request.POST.get('description', '')
        badge.icon = request.POST.get('icon', badge.icon)
        badge.color = request.POST.get('color', badge.color)

        value = request.POST.get('condition_value')
        if value:
            try:
                badge.condition_value = json.loads(value)
            except json.JSONDecodeError:
                messages.error(request, _('JSON invalide pour la condition.'))
                return render(request, 'admin_sidequest/badge_form.html', {'badge': badge, 'form_action': 'edit'})

        if new_slug:
            badge.slug = new_slug
        elif not badge.slug:
            badge.slug = badge.name.lower().replace(' ', '-')

        try:
            badge.full_clean()
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'admin_sidequest/badge_form.html', {'badge': badge, 'form_action': 'edit'})

        try:
            badge.save()
            messages.success(request, _('Badge modifié.'))
            return redirect('admin_sidequest:badges')
        except Exception as e:
            messages.error(request, f'Erreur: {e}')
            return render(request, 'admin_sidequest/badge_form.html', {'badge': badge, 'form_action': 'edit'})

    return render(request, 'admin_sidequest/badge_form.html', {'badge': badge, 'form_action': 'edit'})
