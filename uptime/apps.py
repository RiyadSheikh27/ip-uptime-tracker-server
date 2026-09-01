import sys

from django.apps import AppConfig


class UptimeConfig(AppConfig):
    name = 'uptime'

    def ready(self):
        # Only auto-sync when actually running the dev server - not on
        # migrate, makemigrations, shell, celery, tests, etc.
        if 'runserver' not in sys.argv:
            return

        # runserver's autoreloader spawns a parent process and a child
        # process; ready() fires in both. RUN_MAIN is only set in the
        # child that actually serves requests, so this guard makes sure
        # we sync exactly once instead of twice per save.
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from django.db.utils import OperationalError, ProgrammingError
        from .tasks import sync_monitored_ips_from_env

        try:
            synced = sync_monitored_ips_from_env()
        except (OperationalError, ProgrammingError):
            # Table doesn't exist yet (e.g. first run before migrate).
            # Don't crash the dev server over this - just skip.
            return

        print(f'[uptime] synced {len(synced)} IP(s) from .env')