from django.core.management.base import BaseCommand
from django.db import transaction
from apps.badges.models import Badge


BADGES = [
    # ── PROGRESSION (tasks_completed) ──
    {
        'name': 'Premier Pas',
        'slug': 'first_step',
        'description': 'Première tâche complétée',
        'icon': 'run',
        'color': '#4CAF50',
        'condition_type': Badge.ConditionTypeChoices.TASKS_COMPLETED,
        'condition_value': {'min_tasks': 1},
    },
    {
        'name': 'Lanceur',
        'slug': 'launcher',
        'description': '5 tâches complétées',
        'icon': 'rocket',
        'color': '#2196F3',
        'condition_type': Badge.ConditionTypeChoices.TASKS_COMPLETED,
        'condition_value': {'min_tasks': 5},
    },
    {
        'name': 'Pro',
        'slug': 'pro',
        'description': '20 tâches complétées',
        'icon': 'briefcase',
        'color': '#9C27B0',
        'condition_type': Badge.ConditionTypeChoices.TASKS_COMPLETED,
        'condition_value': {'min_tasks': 20},
    },
    {
        'name': 'Elite',
        'slug': 'elite',
        'description': '50 tâches complétées',
        'icon': 'trophy',
        'color': '#FF9800',
        'condition_type': Badge.ConditionTypeChoices.TASKS_COMPLETED,
        'condition_value': {'min_tasks': 50},
    },
    {
        'name': 'Légende',
        'slug': 'legend',
        'description': '100 tâches complétées',
        'icon': 'crown',
        'color': '#F44336',
        'condition_type': Badge.ConditionTypeChoices.TASKS_COMPLETED,
        'condition_value': {'min_tasks': 100},
    },
    # ── QUALITÉ (custom → review_count) ──
    {
        'name': 'Bien noté',
        'slug': 'well_rated',
        'description': '5 avis 5 étoiles reçus',
        'icon': 'star',
        'color': '#FFC107',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'review_count', 'min_reviews': 5}]},
    },
    {
        'name': 'Excellente réputation',
        'slug': 'top_rated',
        'description': '10 avis 5 étoiles reçus',
        'icon': 'star-half',
        'color': '#FF6F00',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'review_count', 'min_reviews': 10}]},
    },
    {
        'name': 'Intouchable',
        'slug': 'untouchable',
        'description': '25 avis 5 étoiles reçus',
        'icon': 'award',
        'color': '#E91E63',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'review_count', 'min_reviews': 25}]},
    },
    # ── RÉGULARITÉ (custom → streak) ──
    {
        'name': 'En feu',
        'slug': 'on_fire',
        'description': 'Actif 2 semaines consécutives',
        'icon': 'flame',
        'color': '#FF5722',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'streak', 'min_streak': 14}]},
    },
    {
        'name': 'Régulier',
        'slug': 'regular',
        'description': 'Actif 4 semaines consécutives',
        'icon': 'bolt',
        'color': '#3F51B5',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'streak', 'min_streak': 28}]},
    },
    {
        'name': 'Inarrêtable',
        'slug': 'unstoppable',
        'description': 'Actif 8 semaines consécutives',
        'icon': 'shield-check',
        'color': '#009688',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'streak', 'min_streak': 56}]},
    },
    # ── SPÉCIALISATION (custom → tasks_in_category) ──
    {
        'name': 'Spécialiste',
        'slug': 'specialist',
        'description': '10 tâches dans la même catégorie',
        'icon': 'target',
        'color': '#607D8B',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'tasks_in_category', 'min_count': 10}]},
    },
    {
        'name': 'Expert',
        'slug': 'expert',
        'description': '25 tâches dans la même catégorie',
        'icon': 'tool',
        'color': '#795548',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'tasks_in_category', 'min_count': 25}]},
    },
    # ── CONFIANCE (custom → verified) ──
    {
        'name': 'Vérifié',
        'slug': 'verified',
        'description': 'Compte vérifié par l\'administrateur',
        'icon': 'circle-check',
        'color': '#00BCD4',
        'condition_type': Badge.ConditionTypeChoices.CUSTOM,
        'condition_value': {'checks': [{'type': 'verified'}]},
    },
]


class Command(BaseCommand):
    help = 'Crée les 14 badges de gamification SideQuest.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        with transaction.atomic():
            for data in BADGES:
                slug = data['slug']
                if Badge.objects.filter(slug=slug).exists():
                    self.stdout.write(f'[SKIP] {slug} — existe déjà')
                    skipped += 1
                    continue

                Badge.objects.create(
                    name=data['name'],
                    slug=data['slug'],
                    description=data['description'],
                    icon=data['icon'],
                    color=data['color'],
                    condition_type=data['condition_type'],
                    condition_value=data['condition_value'],
                    is_active=True,
                    target_role=Badge.TargetRoleChoices.TASKER,
                )
                self.stdout.write(f'[CRÉÉ] {data["name"]} ({slug})')
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nTerminé : {created} créé(s), {skipped} ignoré(s) sur {len(BADGES)} badges.'
        ))
