from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'
    verbose_name = 'Tâches & Missions'

    def ready(self):
        import apps.tasks.signals  # noqa: F401
