from django.core.management.base import BaseCommand
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Bumps the application version number.'

    def add_arguments(self, parser):
        parser.add_argument('new_version', type=str, help='The new version number (e.g., 1.2.0)')

    def handle(self, *args, **kwargs):
        new_version = kwargs['new_version']
        version_file = Path(__file__).resolve().parent.parent.parent.parent / 'VERSION'

        with open(version_file, 'w') as f:
            f.write(new_version)

        self.stdout.write(self.style.SUCCESS(f"Version bumped to {new_version}"))
