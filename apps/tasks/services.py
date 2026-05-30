from apps.tasks.models import Task


def get_tasker_tasks(tasker):
    return Task.objects.filter(
        assigned_tasker=tasker,
    ).exclude(status__in=[
        Task.StatusChoices.CANCELLED,
        Task.StatusChoices.CLOSED,
    ]).order_by('-updated_at')


def get_client_tasks(client):
    return Task.objects.filter(client=client).order_by('-created_at')