# Generated manually
import uuid
from django.db import migrations, models
import django.db.models.deletion


def populate_application(apps, schema_editor):
    Conversation = apps.get_model('messaging', 'Conversation')
    TaskApplication = apps.get_model('tasks', 'TaskApplication')

    for conv in Conversation.objects.all():
        try:
            app = TaskApplication.objects.get(
                task=conv.task,
                tasker=conv.tasker,
            )
            conv.application = app
            conv.save(update_fields=['application'])
        except TaskApplication.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_closed_at_alter_task_arrival_lat_and_more'),
        ('messaging', '0002_conversation_is_closed_conversation_is_reported_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='application',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversation',
                to='tasks.taskapplication',
                verbose_name='candidature',
            ),
        ),
        migrations.RunPython(populate_application, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='conversation',
            name='application',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversation',
                to='tasks.taskapplication',
                verbose_name='candidature',
            ),
        ),
        migrations.RemoveField(
            model_name='conversation',
            name='task',
        ),
    ]
