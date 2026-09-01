from django.core.management.base import BaseCommand
from uptime.tasks import sync_monitored_ips_from_env


class Command(BaseCommand):
    help = 'Sync IPs from environment to database'

    def handle(self, *args, **options):
        result = sync_monitored_ips_from_env()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully synced {len(result)} IPs: {", ".join(result)}')
        )
