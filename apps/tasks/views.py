from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import client_required, tasker_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Count, Prefetch, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
import json
import urllib.parse
import urllib.request

from apps.tasks.models import Task, TaskApplication, TaskProof, Category, SubCategory
from apps.tasks.forms import TaskCreateForm, TaskProofForm, ProofReviewForm
from apps.messaging.forms import MessageForm
from apps.tasks.services import get_tasker_tasks, get_client_tasks
from apps.messaging.models import Conversation, Message
from apps.accounts.models import CustomUser, Notification, UserProfile
from apps.reputation.models import Review
from apps.badges.models import Badge
from apps.badges.engine import check_and_award_badges


LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500]


def create_notification(user, title, message, n_type, related_task=None, related_conversation=None, related_review=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=n_type,
        related_task=related_task,
        related_conversation=related_conversation,
        related_review=related_review,
    )


def award_xp(user, amount):
    profile = user.profile
    profile.xp += amount
    new_level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if profile.xp >= threshold:
            new_level = i + 1
    if new_level > profile.level:
        profile.level = new_level
    profile.save(update_fields=['xp', 'level'])


@login_required
@client_required
def client_dashboard(request):
    tasks = get_client_tasks(request.user)
    drafts = tasks.filter(status=Task.StatusChoices.DRAFT)
    published = tasks.filter(status=Task.StatusChoices.PUBLISHED)
    accepted = tasks.filter(status=Task.StatusChoices.ACCEPTED)
    in_progress = tasks.filter(status__in=[
        Task.StatusChoices.IN_PROGRESS,
        Task.StatusChoices.COMPLETED,
        Task.StatusChoices.AWAITING_CONFIRMATION,
    ])
    finished = tasks.filter(status__in=[
        Task.StatusChoices.VALIDATED,
        Task.StatusChoices.EVALUATED,
        Task.StatusChoices.CLOSED,
        Task.StatusChoices.LITIGE,
        Task.StatusChoices.RESOLVED,
        Task.StatusChoices.REJECTED,
        Task.StatusChoices.CANCELLED,
    ])

    task_app_map = {}
    task_accepted_conv_map = {}
    task_ids = list(tasks.values_list('id', flat=True))
    for app in TaskApplication.objects.filter(task_id__in=task_ids).select_related('conversation', 'task'):
        if app.task_id not in task_app_map:
            task_app_map[app.task_id] = []
        if hasattr(app, 'conversation'):
            task_app_map[app.task_id].append(app.conversation)
            if app.task.assigned_tasker_id and app.tasker_id == app.task.assigned_tasker_id:
                task_accepted_conv_map[app.task_id] = app.conversation

    top_taskers = UserProfile.objects.filter(
        user__role__in=['tasker', 'both'],
        tasks_completed__gt=0,
    ).select_related('user').order_by('-tasker_rating_avg', '-tasks_completed')[:5]

    context = {
        'tasks': tasks,
        'dashboard_tasks': tasks[:2],
        'drafts': drafts,
        'published': published,
        'accepted': accepted,
        'in_progress': in_progress,
        'finished': finished,
        'task_app_map': task_app_map,
        'task_accepted_conv_map': task_accepted_conv_map,
        'user_badges': request.user.badges_earned.select_related('badge').filter(
            badge__target_role__in=['client', 'both']
        ).order_by('-earned_at')[:10],
        'top_taskers': top_taskers,
    }
    return render(request, 'tasks/client_dashboard.html', context)


@login_required
@client_required
def client_quests(request):
    tasks = get_client_tasks(request.user)
    drafts = tasks.filter(status=Task.StatusChoices.DRAFT)
    published = tasks.filter(status=Task.StatusChoices.PUBLISHED)
    accepted = tasks.filter(status=Task.StatusChoices.ACCEPTED)
    in_progress = tasks.filter(status__in=[
        Task.StatusChoices.IN_PROGRESS,
        Task.StatusChoices.COMPLETED,
        Task.StatusChoices.AWAITING_CONFIRMATION,
    ])
    finished = tasks.filter(status__in=[
        Task.StatusChoices.VALIDATED,
        Task.StatusChoices.EVALUATED,
        Task.StatusChoices.CLOSED,
        Task.StatusChoices.LITIGE,
        Task.StatusChoices.RESOLVED,
        Task.StatusChoices.REJECTED,
        Task.StatusChoices.CANCELLED,
    ])

    task_app_map = {}
    task_accepted_conv_map = {}
    task_ids = list(tasks.values_list('id', flat=True))
    for app in TaskApplication.objects.filter(task_id__in=task_ids).select_related('conversation', 'task'):
        if app.task_id not in task_app_map:
            task_app_map[app.task_id] = []
        if hasattr(app, 'conversation'):
            task_app_map[app.task_id].append(app.conversation)
            if app.task.assigned_tasker_id and app.tasker_id == app.task.assigned_tasker_id:
                task_accepted_conv_map[app.task_id] = app.conversation

    top_taskers = UserProfile.objects.filter(
        user__role__in=['tasker', 'both'],
        tasks_completed__gt=0,
    ).select_related('user').order_by('-tasker_rating_avg', '-tasks_completed')[:5]

    status_param = request.GET.get('status', 'all')
    active_tab = status_param if status_param in ['drafts', 'published', 'in_progress', 'finished'] else 'all'

    context = {
        'tasks': tasks,
        'drafts': drafts,
        'published': published,
        'accepted': accepted,
        'in_progress': in_progress,
        'finished': finished,
        'task_app_map': task_app_map,
        'task_accepted_conv_map': task_accepted_conv_map,
        'user_badges': request.user.badges_earned.select_related('badge').filter(
            badge__target_role__in=['client', 'both']
        ).order_by('-earned_at')[:10],
        'top_taskers': top_taskers,
        'active_tab': active_tab,
    }
    return render(request, 'tasks/client_quests.html', context)


@login_required
@tasker_required
def tasker_dashboard(request):
    tasks = get_tasker_tasks(request.user)
    active_tasks = tasks.filter(status__in=[
        Task.StatusChoices.ACCEPTED,
        Task.StatusChoices.IN_PROGRESS,
        Task.StatusChoices.AWAITING_CONFIRMATION,
    ]).select_related('proof')
    finished_tasks = Task.objects.filter(
        assigned_tasker=request.user,
        status__in=[
            Task.StatusChoices.COMPLETED,
            Task.StatusChoices.VALIDATED,
            Task.StatusChoices.EVALUATED,
            Task.StatusChoices.CLOSED,
            Task.StatusChoices.LITIGE,
            Task.StatusChoices.RESOLVED,
            Task.StatusChoices.REJECTED,
            Task.StatusChoices.CANCELLED,
        ],
    ).prefetch_related(Prefetch(
        'reviews',
        queryset=Review.objects.filter(review_type='client_to_tasker'),
        to_attr='client_review',
    )).order_by('-updated_at')

    my_applied_ids = TaskApplication.objects.filter(
        tasker=request.user
    ).values_list('task_id', flat=True)

    available_tasks = Task.objects.filter(
        status=Task.StatusChoices.PUBLISHED,
        assigned_tasker__isnull=True,
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=timezone.now())
    ).exclude(
        client=request.user
    ).exclude(
        id__in=my_applied_ids
    ).select_related('client', 'category').order_by('-published_at')

    total_available = available_tasks.count()
    categories = Category.objects.filter(is_active=True)

    top_taskers = UserProfile.objects.filter(
        user__role__in=['tasker', 'both'],
        tasks_completed__gt=0,
    ).select_related('user').order_by('-tasker_rating_avg', '-tasks_completed')[:5]

    user_badges = request.user.badges_earned.select_related('badge').filter(
        badge__target_role__in=['tasker', 'both']
    ).order_by('-earned_at')[:8]

    my_applications = TaskApplication.objects.filter(
        tasker=request.user
    ).exclude(
        status=TaskApplication.StatusChoices.ACCEPTED
    ).select_related('task', 'task__client').order_by('-created_at')

    now = timezone.now()
    week_start = now - timezone.timedelta(days=now.weekday())
    month_start = now.replace(day=1)
    paid_statuses = [
        Task.StatusChoices.VALIDATED,
        Task.StatusChoices.RESOLVED,
        Task.StatusChoices.EVALUATED,
        Task.StatusChoices.CLOSED,
    ]
    earnings_week = Task.objects.filter(
        assigned_tasker=request.user,
        status__in=paid_statuses,
        updated_at__gte=week_start,
    ).aggregate(total=Sum('reward'))['total'] or 0
    earnings_month = Task.objects.filter(
        assigned_tasker=request.user,
        status__in=paid_statuses,
        updated_at__gte=month_start,
    ).aggregate(total=Sum('reward'))['total'] or 0

    context = {
        'tasks': tasks,
        'active_tasks': active_tasks,
        'finished_tasks': finished_tasks,
        'available_tasks': available_tasks,
        'top_taskers': top_taskers,
        'user_badges': user_badges,
        'my_applications': my_applications,
        'earnings_week': earnings_week,
        'earnings_month': earnings_month,
        'total_available': total_available,
        'categories': categories,
    }
    return render(request, 'tasks/tasker_dashboard.html', context)


@login_required
@tasker_required
def tasker_profile(request):
    profile = request.user.profile
    user_badges = request.user.badges_earned.select_related('badge').filter(
        badge__target_role__in=['tasker', 'both']
    ).order_by('-earned_at')
    all_badges = Badge.objects.filter(
        is_active=True,
        target_role__in=['tasker', 'both'],
    )
    earned_slugs = set(user_badges.values_list('badge__slug', flat=True))

    context = {
        'user_badges': user_badges,
        'all_badges': all_badges,
        'earned_slugs': earned_slugs,
        'profile': profile,
    }
    return render(request, 'tasks/tasker_profile.html', context)


@login_required
@tasker_required
def tasker_leaderboard(request):
    top_taskers = UserProfile.objects.filter(
        user__role__in=['tasker', 'both'],
        tasks_completed__gt=0,
    ).select_related('user').order_by('-tasker_rating_avg', '-tasks_completed')[:50]

    user_rank = None
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
        all_ranked = list(UserProfile.objects.filter(
            user__role__in=['tasker', 'both'],
            tasks_completed__gt=0,
        ).order_by('-tasker_rating_avg', '-tasks_completed'))
        for idx, p in enumerate(all_ranked):
            if p.id == user_profile.id:
                user_rank = idx + 1
                break

    context = {
        'top_taskers': top_taskers,
        'user_rank': user_rank,
        'user_profile': user_profile,
    }
    return render(request, 'tasks/tasker_leaderboard.html', context)


@login_required
@tasker_required
def tasker_missions(request):
    now = timezone.now()
    base_qs = Task.objects.filter(assigned_tasker=request.user).select_related('category', 'proof')

    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    price_sort = request.GET.get('price', '')
    rating_filter = request.GET.get('rating', '')
    category_filter = request.GET.get('category', '')

    show_applications = (status_filter == 'applications')
    show_saved = (status_filter == 'saved')

    if show_saved:
        saved_ids = request.user.profile.saved_tasks.values_list('id', flat=True)
        base_qs = Task.objects.filter(id__in=saved_ids).select_related('category')
        applications = TaskApplication.objects.none()
    elif show_applications:
        applications = TaskApplication.objects.filter(
            tasker=request.user,
            status=TaskApplication.StatusChoices.PENDING,
        ).select_related('task__category').order_by('-created_at')
    else:
        applications = TaskApplication.objects.none()

    if status_filter == 'completed':
        base_qs = base_qs.filter(status__in=[
            Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED,
            Task.StatusChoices.CLOSED, Task.StatusChoices.RESOLVED,
            Task.StatusChoices.REJECTED,
        ])
    elif status_filter == 'cancelled':
        base_qs = base_qs.filter(status=Task.StatusChoices.CANCELLED)
    elif status_filter == 'in_progress':
        base_qs = base_qs.filter(status__in=[
            Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS,
            Task.StatusChoices.AWAITING_CONFIRMATION, Task.StatusChoices.COMPLETED,
        ])

    if date_filter:
        cutoff = now - timezone.timedelta(days={
            'week': 7, 'month': 30, '3months': 90,
        }.get(date_filter, 0))
        base_qs = base_qs.filter(updated_at__gte=cutoff)

    if price_sort == 'asc':
        base_qs = base_qs.order_by('reward')
    elif price_sort == 'desc':
        base_qs = base_qs.order_by('-reward')
    else:
        base_qs = base_qs.order_by('-updated_at')

    if rating_filter == '5':
        base_qs = base_qs.filter(
            reviews__review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            reviews__reviewed=request.user,
            reviews__rating=5,
        )
    elif rating_filter == '4+':
        base_qs = base_qs.filter(
            reviews__review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            reviews__reviewed=request.user,
            reviews__rating__gte=4,
        )
    elif rating_filter == '3+':
        base_qs = base_qs.filter(
            reviews__review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            reviews__reviewed=request.user,
            reviews__rating__gte=3,
        )
    elif rating_filter == 'unrated':
        base_qs = base_qs.exclude(
            reviews__review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            reviews__reviewed=request.user,
        )

    if category_filter:
        base_qs = base_qs.filter(category__slug=category_filter)

    missions = base_qs.prefetch_related(
        Prefetch(
            'reviews',
            queryset=Review.objects.filter(
                reviewed=request.user,
                review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
                moderation_status=Review.ModerationStatusChoices.VALIDATED,
            ),
            to_attr='tasker_rating_received'
        ),
    )

    categories = Category.objects.filter(is_active=True)

    all_missions = Task.objects.filter(assigned_tasker=request.user)
    active_count = all_missions.filter(status__in=[
        Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS,
        Task.StatusChoices.AWAITING_CONFIRMATION, Task.StatusChoices.COMPLETED,
    ]).count()
    completed_count = all_missions.filter(status__in=[
        Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED,
        Task.StatusChoices.CLOSED, Task.StatusChoices.RESOLVED,
        Task.StatusChoices.REJECTED,
    ]).count()
    pending_count = all_missions.filter(status=Task.StatusChoices.PUBLISHED).count()
    applications_count = TaskApplication.objects.filter(
        tasker=request.user,
        status=TaskApplication.StatusChoices.PENDING,
    ).count()
    saved_count = request.user.profile.saved_tasks.count()

    context = {
        'missions': [] if show_applications else missions,
        'applications': applications,
        'categories': categories,
        'total_count': missions.count(),
        'active_count': active_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'applications_count': applications_count,
        'saved_count': saved_count,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'price_sort': price_sort,
        'rating_filter': rating_filter,
        'category_filter': category_filter,
    }
    return render(request, 'tasks/tasker_missions.html', context)


@login_required
@tasker_required
def task_toggle_save(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    profile = request.user.profile
    if profile.saved_tasks.filter(id=task_id).exists():
        profile.saved_tasks.remove(task)
        saved = False
    else:
        profile.saved_tasks.add(task)
        saved = True
    return JsonResponse({'saved': saved})


@login_required
@client_required
def task_create(request):
    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.client = request.user
            action = request.POST.get('action')
            if action == 'publish':
                task.status = Task.StatusChoices.PUBLISHED
            else:
                task.status = Task.StatusChoices.DRAFT
            task.save()
            messages.success(request, _('Tâche créée avec succès.'))
            return redirect('tasks:client_dashboard')
    else:
        form = TaskCreateForm()
    return render(request, 'tasks/task_create.html', {'form': form})


@login_required
@client_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    if request.method == 'POST':
        form = TaskCreateForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            action = request.POST.get('action')
            if action == 'publish' and task.status == Task.StatusChoices.DRAFT:
                task.status = Task.StatusChoices.PUBLISHED
            task.save()
            messages.success(request, _('Tâche mise à jour.'))
            return redirect('tasks:client_dashboard')
    else:
        form = TaskCreateForm(instance=task)
    return render(request, 'tasks/task_edit.html', {'form': form})


@login_required
@client_required
def task_publish(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    if task.status == Task.StatusChoices.DRAFT:
        task.status = Task.StatusChoices.PUBLISHED
        task.save()
        messages.success(request, _('Tâche publiée avec succès.'))
    return redirect('tasks:client_dashboard')


@login_required
@client_required
def task_cancel(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    if task.status == Task.StatusChoices.PUBLISHED:
        task.status = Task.StatusChoices.CANCELLED
        task.save()
        profile = request.user.profile
        profile.tasks_cancelled += 1
        profile.save(update_fields=['tasks_cancelled'])
        messages.success(request, _('Tâche annulée.'))
    return redirect('tasks:client_dashboard')


@login_required
@client_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    if task.status == Task.StatusChoices.DRAFT:
        task.delete()
        messages.success(request, _('Tâche supprimée.'))
    return redirect('tasks:client_dashboard')


@login_required
def task_list(request):
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    location = request.GET.get('location', '').strip()
    search_performed = request.GET.get('search') == '1'

    from django.utils import timezone
    now = timezone.now()
    tasks = Task.objects.filter(
        status=Task.StatusChoices.PUBLISHED
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    )

    if q:
        tasks = tasks.filter(title__icontains=q)
    if category_slug:
        tasks = tasks.filter(category__slug=category_slug)
    if location:
        tasks = tasks.filter(
            Q(arrival_address__icontains=location) |
            Q(departure_address__icontains=location)
        )

    tasks = tasks.order_by('-published_at')
    paginator = Paginator(tasks, 12)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    categories = Category.objects.filter(is_active=True)

    return render(request, 'tasks/task_list.html', {
        'page_obj': page_obj,
        'tasks': page_obj,
        'categories': categories,
        'search_q': q,
        'search_category': category_slug,
        'search_location': location,
        'search_performed': search_performed,
    })


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    context = {'task': task}

    if request.user == task.client:
        context['is_owner'] = True
        context['can_apply'] = False
        if task.status == Task.StatusChoices.PUBLISHED:
            context['applications'] = task.applications.filter(status=TaskApplication.StatusChoices.PENDING).select_related('conversation')
    elif request.user.acting_as_tasker() and task.status == Task.StatusChoices.PUBLISHED and not task.is_expired:
        already_applied = TaskApplication.objects.filter(task=task, tasker=request.user).exists()
        context['can_apply'] = not already_applied

    return render(request, 'tasks/task_detail.html', context)


@login_required
@tasker_required
def task_apply(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.status != Task.StatusChoices.PUBLISHED or task.is_expired:
        messages.error(request, _('Cette tâche n\'est plus disponible.'))
        if request.htmx:
            return HttpResponse('<div style="display:none;" hx-swap-oob="true"></div>')
        return redirect('tasks:task_list')

    if request.user == task.client:
        messages.error(request, _('Vous ne pouvez pas postuler à votre propre tâche.'))
        if request.htmx:
            return HttpResponse('<div style="display:none;" hx-swap-oob="true"></div>')
        return redirect('tasks:task_detail', task_id=task.id)

    if TaskApplication.objects.filter(task=task, tasker=request.user).exists():
        messages.info(request, _('Vous avez déjà postulé à cette tâche.'))
        if request.htmx:
            return HttpResponse('<div style="display:none;" hx-swap-oob="true"></div>')
        return redirect('tasks:tasker_dashboard')

    message = request.POST.get('message', '')
    try:
        application = TaskApplication.objects.create(
            task=task,
            tasker=request.user,
            message=message,
        )
    except IntegrityError:
        messages.info(request, _('Vous avez déjà postulé à cette tâche.'))
        if request.htmx:
            return HttpResponse('<div style="display:none;" hx-swap-oob="true"></div>')
        return redirect('tasks:tasker_dashboard')

    Conversation.objects.create(
        application=application,
        client=task.client,
        tasker=request.user,
    )

    create_notification(
        task.client,
        _('Nouvelle candidature'),
        _(f'{request.user.full_name} a postulé à "{task.title}".'),
        Notification.TypeChoices.NEW_APPLICATION,
        related_task=task,
    )
    task.notify_client_new_application(application)

    if request.htmx:
        resp = '<div style="padding:1rem;text-align:center;color:var(--sq-success);font-weight:600;background:var(--sq-surface);border:1px dashed var(--sq-primary-light);border-radius:14px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Candidature envoyée !</div>'
        return HttpResponse(resp)

    messages.success(request, _('Candidature envoyée ! Vous pouvez discuter avec le client.'))
    return redirect('tasks:tasker_dashboard')


@login_required
@client_required
def task_choose_tasker(request, task_id, application_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    application = get_object_or_404(TaskApplication, id=application_id, task=task)

    try:
        task.accept_tasker(application.tasker)
    except ValidationError:
        messages.error(request, _('Cette tâche n\'est plus en attente de candidatures.'))
        return redirect('tasks:client_dashboard')

    application.accept()

    create_notification(
        application.tasker,
        _('Mission acceptée !'),
        _(f'Votre candidature pour "{task.title}" a été acceptée par le client.'),
        Notification.TypeChoices.TASK_ACCEPTED,
        related_task=task,
    )

    messages.success(request, _(f'Tasker {application.tasker.full_name} choisi !'))
    return redirect('tasks:client_dashboard')


@login_required
@client_required
def task_reject_application(request, task_id, application_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)
    application = get_object_or_404(TaskApplication, id=application_id, task=task)

    application.reject()
    messages.success(request, _('Candidature rejetée.'))
    return redirect('tasks:task_detail', task_id=task_id)


@login_required
@tasker_required
def task_cancel_application(request, task_id, application_id):
    application = get_object_or_404(TaskApplication, id=application_id, tasker=request.user)

    if application.status != TaskApplication.StatusChoices.PENDING:
        messages.error(request, _('Vous ne pouvez annuler qu\'une candidature en attente.'))
        return redirect(request.META.get('HTTP_REFERER', 'tasks:tasker_missions'))

    application.delete()
    messages.success(request, _('Candidature annulée.'))
    return redirect(request.META.get('HTTP_REFERER', 'tasks:tasker_missions'))


@login_required
def task_workspace(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.user != task.client and request.user != task.assigned_tasker and not request.user.is_admin():
        return HttpResponseForbidden(_("Vous n'avez pas accès à cet espace de travail."))

    conversation = None
    try:
        app = TaskApplication.objects.get(task=task, status='accepted')
        conversation = getattr(app, 'conversation', None)
    except TaskApplication.DoesNotExist:
        pass

    is_tasker = request.user == task.assigned_tasker
    existing_proof = getattr(task, 'proof', None)
    is_revision = existing_proof and existing_proof.client_review == TaskProof.ReviewChoices.REVISION_REQUESTED

    if conversation and request.method == 'GET':
        from apps.messaging.models import Message
        Message.objects.filter(
            conversation=conversation, is_read=False,
        ).exclude(sender=request.user).update(is_read=True)
        Notification.objects.filter(
            user=request.user,
            type=Notification.TypeChoices.MESSAGE_RECEIVED,
            related_conversation=conversation,
            is_read=False,
        ).update(is_read=True)

    chat_form = MessageForm()
    proof_photos_required = task.proof_required and not is_revision
    proof_form = TaskProofForm(proof_required=proof_photos_required)
    review_form = ProofReviewForm()

    if request.method == 'POST':
        # Chat message
        if 'send_message' in request.POST and conversation and not conversation.is_closed:
            chat_form = MessageForm(request.POST)
            if chat_form.is_valid():
                msg = chat_form.save(commit=False)
                msg.conversation = conversation
                msg.sender = request.user
                msg.save()
                conversation.save(update_fields=['last_activity_at'])

                recipient = conversation.other_participant(request.user)
                Notification.objects.create(
                    user=recipient,
                    type=Notification.TypeChoices.MESSAGE_RECEIVED,
                    title=_('Nouveau message'),
                    message=_('Vous avez reçu un nouveau message de la part de %(sender)s au sujet de « %(task)s »') % {
                        'sender': request.user.full_name,
                        'task': conversation.task.title,
                    },
                    related_conversation=conversation,
                )
                if request.htmx:
                    return render(request, 'messaging/snippets/message_bubble.html', {
                        'message': msg, 'request_user': request.user,
                    })
                return redirect('tasks:task_workspace', task_id=task.id)

        # Tasker completes mission without proof
        elif 'complete_mission' in request.POST and is_tasker and not task.proof_required and (
            task.status in (Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS)
        ):
            if task.status == Task.StatusChoices.ACCEPTED:
                task.start()
            task.await_confirmation()
            create_notification(
                task.client, _('Mission terminée !'),
                _(f'{request.user.full_name} a terminé "{task.title}". Confirmez la fin de mission.'),
                Notification.TypeChoices.TASK_COMPLETED, related_task=task,
            )
            messages.success(request, _('Mission marquée comme terminée !'))
            return redirect(reverse('tasks:task_workspace', kwargs={'task_id': task.id}) + '?tab=mission')

        # Tasker submits proof
        elif 'submit_proof' in request.POST and is_tasker and task.proof_required and (
            task.status in (Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS) or is_revision
        ):
            first_submission = not existing_proof and task.status in (Task.StatusChoices.ACCEPTED, Task.StatusChoices.IN_PROGRESS)
            revision_resubmission = is_revision and existing_proof
            if not first_submission and not revision_resubmission:
                return redirect(reverse('tasks:task_workspace', kwargs={'task_id': task.id}) + '?tab=proof')

            if task.status == Task.StatusChoices.ACCEPTED:
                task.start()

            # In revision resubmission, photos are optional (existing ones are preserved)
            post_needs_photos = task.proof_required and not revision_resubmission
            proof_form = TaskProofForm(request.POST, request.FILES, proof_required=post_needs_photos)
            if proof_form.is_valid():
                photo_urls = []
                for uploaded_file in request.FILES.getlist('photos'):
                    from django.core.files.storage import default_storage
                    filename = default_storage.save(f'task_proofs/{uploaded_file.name}', uploaded_file)
                    photo_urls.append(default_storage.url(filename))

                if revision_resubmission:
                    existing_proof.description = proof_form.cleaned_data['description']
                    if photo_urls:
                        existing_proof.photos = photo_urls
                    existing_proof.client_review = TaskProof.ReviewChoices.PENDING
                    existing_proof.revision_notes = ''
                    existing_proof.reviewed_at = None
                    existing_proof.save()
                elif first_submission:
                    TaskProof.objects.create(
                        task=task, tasker=request.user,
                        description=proof_form.cleaned_data['description'],
                        photos=photo_urls,
                    )
                task.await_confirmation()
                if revision_resubmission:
                    create_notification(
                        task.client, _('Preuve corrigée soumise'),
                        _(f'Le tasker a soumis une preuve corrigée pour "{task.title}". Vérifiez la modification.'),
                        Notification.TypeChoices.SYSTEM, related_task=task,
                    )
                else:
                    create_notification(
                        task.client, _('Mission terminée !'),
                        _(f'Le tasker a terminé "{task.title}". Vérifiez la preuve.'),
                        Notification.TypeChoices.TASK_COMPLETED, related_task=task,
                    )
                return redirect(reverse('tasks:task_workspace', kwargs={'task_id': task.id}) + '?tab=proof')

        # Client confirms mission completion (without proof)
        elif 'confirm_completion' in request.POST and not is_tasker and not task.proof_required and task.status == Task.StatusChoices.AWAITING_CONFIRMATION:
            action = request.POST.get('completion_action')
            if action == 'accept':
                task.validate()
                accepted_app = TaskApplication.objects.filter(
                    task=task, tasker=task.assigned_tasker
                ).first()
                if accepted_app and hasattr(accepted_app, 'conversation'):
                    accepted_app.conversation.close()
                profile = task.assigned_tasker.profile
                reviews = Review.objects.filter(
                    reviewed=task.assigned_tasker,
                    review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
                    moderation_status=Review.ModerationStatusChoices.VALIDATED,
                )
                avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
                profile.tasker_rating_avg = round(float(avg), 2)
                profile.tasker_rating_count = reviews.count()
                profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count'])
                award_xp(task.assigned_tasker, 50)
                check_and_award_badges(task.assigned_tasker)
                create_notification(
                    task.assigned_tasker, _('Mission validée !'),
                    _(f'Le client a confirmé la fin de "{task.title}".'),
                    Notification.TypeChoices.TASK_COMPLETED, related_task=task,
                )
                Notification.objects.filter(
                    user=request.user,
                    type=Notification.TypeChoices.TASK_COMPLETED,
                    related_task=task,
                    is_read=False,
                ).update(is_read=True)
                messages.success(request, _('Mission confirmée ! Veuillez évaluer le tasker.'))
                return redirect(reverse('tasks:task_evaluate', kwargs={'task_id': task.id}))

            elif action == 'litige':
                notes = request.POST.get('notes', '').strip()
                task.open_litige()
                if conversation:
                    conversation.close()
                msg = _(f'Un litige a été ouvert pour "{task.title}".')
                if notes:
                    msg += _(f' Motif : {notes}')
                create_notification(
                    task.assigned_tasker, _('Litige ouvert'),
                    msg,
                    Notification.TypeChoices.SYSTEM, related_task=task,
                )
                Notification.objects.filter(
                    user=request.user,
                    type=Notification.TypeChoices.TASK_COMPLETED,
                    related_task=task,
                    is_read=False,
                ).update(is_read=True)
                return redirect(reverse('tasks:task_workspace', kwargs={'task_id': task.id}) + '?tab=mission')

        # Client reviews proof
        elif 'review_proof' in request.POST and not is_tasker and existing_proof and task.status == Task.StatusChoices.AWAITING_CONFIRMATION and existing_proof.client_review == TaskProof.ReviewChoices.PENDING:
            review_form = ProofReviewForm(request.POST)
            if review_form.is_valid():
                action = review_form.cleaned_data['action']
                notes = review_form.cleaned_data['notes']
                proof = existing_proof

                if action == 'accept':
                    proof.accept()
                    task.validate()
                    accepted_app = TaskApplication.objects.filter(
                        task=task, tasker=task.assigned_tasker
                    ).first()
                    if accepted_app and hasattr(accepted_app, 'conversation'):
                        accepted_app.conversation.close()
                    profile = task.assigned_tasker.profile
                    reviews = Review.objects.filter(
                        reviewed=task.assigned_tasker,
                        review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
                        moderation_status=Review.ModerationStatusChoices.VALIDATED,
                    )
                    avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
                    profile.tasker_rating_avg = round(float(avg), 2)
                    profile.tasker_rating_count = reviews.count()
                    profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count'])
                    award_xp(task.assigned_tasker, 50)
                    check_and_award_badges(task.assigned_tasker)
                    create_notification(
                        task.assigned_tasker, _('Preuve validée !'),
                        _(f'Le client a validé votre preuve pour "{task.title}".'),
                        Notification.TypeChoices.TASK_COMPLETED, related_task=task,
                    )

                elif action == 'revision':
                    proof.request_revision(notes)
                    task.status = Task.StatusChoices.IN_PROGRESS
                    task.save(update_fields=['status', 'updated_at'])
                    create_notification(
                        task.assigned_tasker, _('Modification demandée'),
                        _(f'Le client demande des modifications pour "{task.title}" : {notes}'),
                        Notification.TypeChoices.SYSTEM, related_task=task,
                    )

                elif action == 'reject':
                    proof.client_review = TaskProof.ReviewChoices.REJECTED
                    proof.revision_notes = notes
                    proof.reviewed_at = timezone.now()
                    proof.save()
                    task.reject()
                    if conversation:
                        conversation.close()
                    create_notification(
                        task.assigned_tasker, _('Preuve refusée'),
                        _(f'Le client a refusé votre preuve pour "{task.title}".'),
                        Notification.TypeChoices.SYSTEM, related_task=task,
                    )

                elif action == 'litige':
                    proof.client_review = TaskProof.ReviewChoices.REJECTED
                    proof.revision_notes = notes
                    proof.reviewed_at = timezone.now()
                    proof.save()
                    task.open_litige()
                    if conversation:
                        conversation.close()
                    create_notification(
                        task.assigned_tasker, _('Litige ouvert'),
                        _(f'Un litige a été ouvert pour "{task.title}".'),
                        Notification.TypeChoices.SYSTEM, related_task=task,
                    )

                # Mark related notifications as read so the client can't re-review from a notification
                Notification.objects.filter(
                    user=request.user,
                    type__in=[Notification.TypeChoices.TASK_COMPLETED, Notification.TypeChoices.SYSTEM],
                    related_task=task,
                    is_read=False,
                ).update(is_read=True)

                return redirect(reverse('tasks:task_workspace', kwargs={'task_id': task.id}) + '?tab=proof')

    messages_qs = conversation.messages.order_by('created_at') if conversation else []

    is_admin = request.user.is_admin()
    if is_admin:
        base_template = 'base_admin.html'
    else:
        base_template = 'base_tasker.html' if is_tasker else 'base_client.html'
    context = {
        'task': task,
        'conversation': conversation,
        'chat_messages': messages_qs,
        'chat_form': chat_form,
        'proof_form': proof_form,
        'review_form': review_form,
        'existing_proof': existing_proof,
        'is_revision': is_revision,
        'is_tasker': is_tasker,
        'is_admin': is_admin,
        'base_template': base_template,
    }
    return render(request, 'tasks/task_workspace.html', context)


@login_required
@tasker_required
def task_start(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_tasker=request.user)

    if task.status != Task.StatusChoices.ACCEPTED:
        messages.error(request, _('Vous ne pouvez pas démarrer cette tâche.'))
        return redirect('tasks:tasker_dashboard')

    task.start()
    messages.success(request, _('Mission démarrée !'))
    return redirect('tasks:tasker_dashboard')





@login_required
@client_required
def task_review_proof(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)

    if not task.proof_required:
        messages.error(request, _('Cette tâche ne nécessite pas de preuve.'))
        return redirect('tasks:client_dashboard')

    if not hasattr(task, 'proof'):
        messages.error(request, _('Aucune preuve à réviser.'))
        return redirect('tasks:client_dashboard')

    proof = task.proof
    already_reviewed = proof.client_review != TaskProof.ReviewChoices.PENDING

    if request.method == 'POST':
        if task.status != Task.StatusChoices.AWAITING_CONFIRMATION or already_reviewed:
            messages.error(request, _('Cette preuve a déjà été révisée.'))
            return redirect('tasks:client_dashboard')

        form = ProofReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']

            if action == 'accept':
                proof.accept()
                task.validate()

                accepted_app = TaskApplication.objects.filter(
                    task=task, tasker=task.assigned_tasker
                ).first()
                if accepted_app and hasattr(accepted_app, 'conversation'):
                    accepted_app.conversation.close()

                profile = task.assigned_tasker.profile
                reviews = Review.objects.filter(
                    reviewed=task.assigned_tasker,
                    review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
                    moderation_status=Review.ModerationStatusChoices.VALIDATED,
                )
                avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
                profile.tasker_rating_avg = round(float(avg), 2)
                profile.tasker_rating_count = reviews.count()
                profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count'])

                award_xp(task.assigned_tasker, 50)
                check_and_award_badges(task.assigned_tasker)

                messages.success(request, _('Tâche validée !'))
            elif action == 'revision':
                proof.request_revision(notes)
                task.status = Task.StatusChoices.IN_PROGRESS
                task.save(update_fields=['status'])

                create_notification(
                    task.assigned_tasker,
                    _('Modification demandée'),
                    _(f'Le client a demandé une modification pour "{task.title}". Notes : {notes or "Aucune"}'),
                    Notification.TypeChoices.SYSTEM,
                    related_task=task,
                )

                messages.info(request, _('Modification demandée au tasker.'))
            elif action == 'reject':
                proof.client_review = TaskProof.ReviewChoices.REJECTED
                proof.reviewed_at = timezone.now()
                proof.save()
                task.reject()

                accepted_app = TaskApplication.objects.filter(
                    task=task, tasker=task.assigned_tasker
                ).first()
                if accepted_app and hasattr(accepted_app, 'conversation'):
                    accepted_app.conversation.close()

                create_notification(
                    task.assigned_tasker,
                    _('Mission refusée'),
                    _(f'Le client a refusé votre mission "{task.title}".'),
                    Notification.TypeChoices.SYSTEM,
                    related_task=task,
                )

                messages.warning(request, _('Tâche refusée.'))
            elif action == 'litige':
                task.open_litige(notes or 'Litige signalé par le client')

                accepted_app = TaskApplication.objects.filter(
                    task=task, tasker=task.assigned_tasker
                ).first()
                if accepted_app and hasattr(accepted_app, 'conversation'):
                    accepted_app.conversation.close()

                create_notification(
                    task.assigned_tasker,
                    _('Litige ouvert'),
                    _(f'Un litige a été signalé pour "{task.title}". Un administrateur va intervenir.'),
                    Notification.TypeChoices.SYSTEM,
                    related_task=task,
                )

                messages.warning(request, _('Litige ouvert. Un administrateur va intervenir.'))

            # Mark related notifications as read so the client can't re-review from a notification
            Notification.objects.filter(
                user=request.user,
                type__in=[Notification.TypeChoices.TASK_COMPLETED, Notification.TypeChoices.SYSTEM],
                related_task=task,
                is_read=False,
            ).update(is_read=True)

            return redirect('tasks:client_dashboard')
    else:
        form = ProofReviewForm() if not already_reviewed and task.status == Task.StatusChoices.AWAITING_CONFIRMATION else None

    return render(request, 'tasks/task_review_proof.html', {
        'form': form, 'task': task, 'proof': proof, 'already_reviewed': already_reviewed,
    })


@login_required
def task_resolve_litige(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not request.user.is_admin():
        return HttpResponseForbidden()

    if task.status != Task.StatusChoices.LITIGE:
        messages.error(request, _('Cette tâche n\'est pas en litige.'))
        return redirect('tasks:client_dashboard')

    task.resolve_litige()
    messages.success(request, _('Litige résolu. La mission est en statut Résolue, les deux parties peuvent maintenant s\'évaluer.'))
    return redirect('admin_sidequest:dashboard')


@login_required
@client_required
def task_evaluate(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)

    if task.status not in (Task.StatusChoices.VALIDATED, Task.StatusChoices.RESOLVED):
        messages.error(request, _('Vous ne pouvez pas évaluer cette tâche.'))
        return redirect('tasks:client_dashboard')

    existing_review = task.reviews.filter(
        reviewer=request.user,
        review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
        moderation_status=Review.ModerationStatusChoices.VALIDATED,
    ).first()
    if existing_review:
        messages.info(request, _('Cette tâche a déjà été évaluée.'))
        return redirect('tasks:client_dashboard')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 3))
        comment = request.POST.get('comment', '')

        review, created = Review.objects.get_or_create(
            task=task,
            reviewer=request.user,
            defaults={
                'reviewed': task.assigned_tasker,
                'rating': rating,
                'comment': comment,
                'review_type': Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
                'moderation_status': Review.ModerationStatusChoices.VALIDATED,
            }
        )

        if not created:
            review.rating = rating
            review.comment = comment
            review.moderation_status = Review.ModerationStatusChoices.VALIDATED
            review.save()

        task.evaluate()

        profile = task.assigned_tasker.profile
        reviews = Review.objects.filter(
            reviewed=task.assigned_tasker,
            review_type=Review.ReviewTypeChoices.CLIENT_REVIEWS_TASKER,
            moderation_status=Review.ModerationStatusChoices.VALIDATED,
        )
        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        profile.tasker_rating_avg = round(float(avg), 2)
        profile.tasker_rating_count = reviews.count()
        profile.save(update_fields=['tasker_rating_avg', 'tasker_rating_count'])

        create_notification(
            task.assigned_tasker,
            _('Nouvel avis reçu'),
            _(f'Le client a évalué votre mission "{task.title}" avec {rating}/5.'),
            Notification.TypeChoices.REVIEW_RECEIVED,
            related_task=task,
            related_review=review,
        )

        messages.success(request, _('Évaluation envoyée !'))
        return redirect('tasks:client_dashboard')

    return render(request, 'tasks/task_evaluate.html', {'task': task, 'review_url': reverse('reputation:tasker_review_client', args=[task.id])})


@login_required
@client_required
def task_close(request, task_id):
    task = get_object_or_404(Task, id=task_id, client=request.user)

    if task.status not in (Task.StatusChoices.EVALUATED,):
        messages.error(request, _('Cette tâche ne peut pas encore être clôturée.'))
        return redirect('tasks:client_dashboard')

    task.close()
    if task.assigned_tasker:
        create_notification(
            task.assigned_tasker,
            _('Mission clôturée'),
            _(f'La mission "{task.title}" a été clôturée.'),
            Notification.TypeChoices.SYSTEM,
            related_task=task,
        )
    messages.success(request, _('Mission clôturée.'))
    return redirect('tasks:client_dashboard')


def get_subcategories(request, cat_id):
    subs = SubCategory.objects.filter(category_id=cat_id, is_active=True).values('id', 'name')
    data = [{'id': str(s['id']), 'name': s['name']} for s in subs]
    return JsonResponse({'subcategories': data})


@login_required
@login_required
def notifications_list(request):
    if request.user.acting_as_client():
        notif_types = [
            Notification.TypeChoices.NEW_APPLICATION,
            Notification.TypeChoices.TASK_COMPLETED,
            Notification.TypeChoices.REVIEW_RECEIVED,
            Notification.TypeChoices.MESSAGE_RECEIVED,
            Notification.TypeChoices.SYSTEM,
        ]
        base_template = 'base_client.html'
    else:
        notif_types = [
            Notification.TypeChoices.TASK_ACCEPTED,
            Notification.TypeChoices.TASK_PUBLISHED,
            Notification.TypeChoices.TASK_COMPLETED,
            Notification.TypeChoices.REVIEW_RECEIVED,
            Notification.TypeChoices.MESSAGE_RECEIVED,
            Notification.TypeChoices.SYSTEM,
        ]
        base_template = 'base_tasker.html'

    notifications = request.user.notifications.filter(type__in=notif_types)
    unread_count = notifications.filter(is_read=False).count()

    if request.GET.get('count_only') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({'unread_count': unread_count})

    notif_filter = request.GET.get('filter')
    notif_type = request.GET.get('type')

    if notif_filter == 'unread':
        notifications = notifications.filter(is_read=False)

    if notif_type:
        notifications = notifications.filter(type=notif_type)

    notifications = notifications[:50]

    return render(request, 'tasks/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'base_template': base_template,
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_read()
    notification.mark_opened()

    return redirect(request.META.get('HTTP_REFERER', 'tasks:notifications_list'))
