from .models import Notification


CLIENT_NOTIF_TYPES = [
    Notification.TypeChoices.NEW_APPLICATION,
    Notification.TypeChoices.TASK_COMPLETED,
    Notification.TypeChoices.REVIEW_RECEIVED,
    Notification.TypeChoices.MESSAGE_RECEIVED,
    Notification.TypeChoices.SYSTEM,
]

TASKER_NOTIF_TYPES = [
    Notification.TypeChoices.TASK_ACCEPTED,
    Notification.TypeChoices.TASK_PUBLISHED,
    Notification.TypeChoices.TASK_COMPLETED,
    Notification.TypeChoices.REVIEW_RECEIVED,
    Notification.TypeChoices.MESSAGE_RECEIVED,
    Notification.TypeChoices.SYSTEM,
]


def review_notifications(request):
    if not request.user.is_authenticated:
        return {}
    reviews = Notification.objects.filter(
        user=request.user,
        type=Notification.TypeChoices.REVIEW_RECEIVED,
        is_read=False,
        related_review__isnull=False,
    ).select_related('related_review', 'related_task')[:5]
    return {'unread_review_notifs': reviews}


def unread_counts(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.acting_as_client():
        notif_types = CLIENT_NOTIF_TYPES
    else:
        notif_types = TASKER_NOTIF_TYPES

    unread_notifs = Notification.objects.filter(
        user=request.user, type__in=notif_types, is_read=False
    ).exclude(
        type=Notification.TypeChoices.MESSAGE_RECEIVED
    ).count()
    unread_msgs = Notification.objects.filter(
        user=request.user,
        type=Notification.TypeChoices.MESSAGE_RECEIVED,
        is_read=False,
    ).count()

    return {
        'unread_notifications_count': unread_notifs,
        'unread_messages_count': unread_msgs,
    }
