from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import CustomUser
from apps.accounts.utils import send_form_email


class Command(BaseCommand):
    help = 'Send the KaynBricool form email to existing users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            help='Send only to one email address for testing.',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Send to every active user with an email address.',
        )

    def handle(self, *args, **options):
        test_email = options.get('email')
        send_all = options.get('all')

        if bool(test_email) == bool(send_all):
            raise CommandError('Use exactly one option: --email test@example.com or --all')

        users = CustomUser.objects.filter(is_active=True).exclude(email='')
        if test_email:
            users = users.filter(email__iexact=test_email)

        total = users.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No matching users found.'))
            return

        sent = 0
        for user in users.iterator():
            send_form_email(user)
            sent += 1

        self.stdout.write(self.style.SUCCESS(f'Form email sent to {sent} user(s).'))
