import os

env = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')

from .base import *  # noqa: F401,F403
