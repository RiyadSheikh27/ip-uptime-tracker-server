from django.db import models
from django.utils import timezone


class UptimeIP(models.Model):
    """ Represents an IP address or URL being monitored for uptime. """

    STATUS_UP = 'up'
    STATUS_DOWN = 'down'
    STATUS_UNKNOWN = 'unknown'
    STATUS_CHOICES = (
        (STATUS_UP, 'Up'),
        (STATUS_DOWN, 'Down'),
        (STATUS_UNKNOWN, 'Unknown'),
    )

    name = models.CharField(max_length=255)
    url = models.CharField(
        max_length=500,
        unique=True,
        help_text='Full URL including scheme and port, e.g. http://102.22.232.42:8296/',
    )
    check_interval_seconds = models.PositiveIntegerField(
        default=60, help_text='How often (seconds) this IP is checked.'
    )
    timeout_seconds = models.PositiveIntegerField(
        default=30, help_text='Request timeout (seconds) before considered down.'
    )
    is_active = models.BooleanField(default=True, help_text='Uncheck to pause monitoring without deleting.')

    # cached current state, kept in sync by uptime.tasks.check_ip
    current_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_up_at = models.DateTimeField(null=True, blank=True)
    last_down_at = models.DateTimeField(null=True, blank=True)
    last_status_change_at = models.DateTimeField(null=True, blank=True)
    next_check_at = models.DateTimeField(default=timezone.now, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.url})'

    @property
    def current_duration_seconds(self):
        """How long the IP has been in its current status (up or down)."""
        if not self.last_status_change_at:
            return None
        return (timezone.now() - self.last_status_change_at).total_seconds()
