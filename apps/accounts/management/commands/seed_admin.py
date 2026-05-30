from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Crée ou met à jour le compte admin principal'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='sidequests.contact05@gmail.com')
        parser.add_argument('--password', default='admin123')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']

        admin = CustomUser.objects.filter(is_superuser=True).first()
        if admin:
            admin.email = email
            admin.set_password(password)
            admin.save(update_fields=['email', 'password'])
            self.stdout.write(self.style.SUCCESS(f'Admin mis à jour : {email}'))
        else:
            admin = CustomUser.objects.create_superuser(
                email=email,
                password=password,
                full_name='Admin SideQuest',
                role=CustomUser.Roles.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS(f'Admin créé : {email}'))
