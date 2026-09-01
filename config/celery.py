import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Read CELERY_* settings from Django settings.py (see the CELERY_ prefix).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in each installed app (finds monitor/tasks.py).
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
