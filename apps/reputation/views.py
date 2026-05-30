from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, F, DecimalField, Value
from django.utils.translation import gettext_lazy as _
from apps.reputation.models import Review
from apps.reputation.forms import ReviewForm
from apps.accounts.models import CustomUser, UserProfile
from apps.tasks.models import Task


def leaderboard(request):
    taskers = (
        UserProfile.objects.select_related('user')
        .filter(tasks_completed__gt=0)
        .annotate(
            composite_score=(
                F('tasker_rating_avg') * Value(0.5, output_field=DecimalField()) +
                F('tasks_completed') * Value(0.3, output_field=DecimalField()) +
                Count('user__badges_earned') * Value(0.2, output_field=DecimalField())
            )
        )
        .order_by('-composite_score')[:50]
    )

    user_rank = None
    user_profile = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_profile = request.user.profile
        all_ranked = list(
            UserProfile.objects.filter(tasks_completed__gt=0)
            .annotate(
                composite_score=(
                    F('tasker_rating_avg') * Value(0.5, output_field=DecimalField()) +
                    F('tasks_completed') * Value(0.3, output_field=DecimalField()) +
                    Count('user__badges_earned') * Value(0.2, output_field=DecimalField())
                )
            )
            .order_by('-composite_score')
        )
        for idx, p in enumerate(all_ranked):
            if p.id == user_profile.id:
                user_rank = idx + 1
                break

    return render(request, 'reputation/leaderboard.html', {
        'taskers': taskers,
        'user_rank': user_rank,
        'user_profile': user_profile,
    })


@login_required
def tasker_review_client(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_tasker=request.user)

    if task.status not in (
        Task.StatusChoices.VALIDATED, Task.StatusChoices.EVALUATED,
        Task.StatusChoices.RESOLVED, Task.StatusChoices.REJECTED,
        Task.StatusChoices.LITIGE, Task.StatusChoices.CANCELLED,
        Task.StatusChoices.CLOSED,
    ):
        messages.error(request, _('Vous ne pouvez évaluer ce client qu\'après validation, refus ou litige.'))
        return redirect('tasks:tasker_dashboard')

    if Review.objects.filter(task=task, reviewer=request.user, review_type=Review.ReviewTypeChoices.TASKER_REVIEWS_CLIENT).exists():
        messages.info(request, _('Vous avez déjà évalué ce client.'))
        return redirect('tasks:tasker_dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.task = task
            review.reviewer = request.user
            review.reviewed = task.client
            review.review_type = Review.ReviewTypeChoices.TASKER_REVIEWS_CLIENT
            review.moderation_status = Review.ModerationStatusChoices.VALIDATED
            review.save()

            from apps.tasks.views import create_notification
            from apps.accounts.models import Notification
            create_notification(
                task.client,
                _('Nouvel avis reçu'),
                _(f'Le tasker a évalué votre mission "{task.title}" avec {review.rating}/5.'),
                Notification.TypeChoices.REVIEW_RECEIVED,
                related_task=task,
                related_review=review,
            )

            messages.success(request, _('Avis envoyé !'))
            return redirect('tasks:tasker_dashboard')
    else:
        form = ReviewForm()

    return render(request, 'reputation/tasker_review_client.html', {
        'form': form,
        'task': task,
        'client': task.client,
    })


def client_profile(request, client_id):
    client = get_object_or_404(CustomUser, id=client_id)

    reviews = Review.objects.filter(
        reviewed=client,
        review_type=Review.ReviewTypeChoices.TASKER_REVIEWS_CLIENT,
        moderation_status=Review.ModerationStatusChoices.VALIDATED,
    ).select_related('reviewer', 'task').order_by('-created_at')

    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = reviews.count()

    completed_tasks = UserProfile.objects.filter(user=client).values('tasks_completed').first()
    member_since = client.date_joined if hasattr(client, 'date_joined') else None

    return render(request, 'reputation/client_profile.html', {
        'client': client,
        'reviews': reviews,
        'avg_rating': round(float(avg_rating), 1),
        'total_reviews': total_reviews,
        'completed_tasks': completed_tasks['tasks_completed'] if completed_tasks else 0,
        'member_since': member_since,
    })
