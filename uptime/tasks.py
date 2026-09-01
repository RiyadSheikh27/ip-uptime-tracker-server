import logging
import time

import requests
from celery import shared_task
from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone

from .models import UptimeIP

logger = logging.getLogger(__name__)


def get_monitored_ips_from_env():
    configured_value = getattr(settings, 'MONITORED_IPS', '')
    if isinstance(configured_value, str):
        return [item.strip() for item in configured_value.split(',') if item.strip()]

    return [str(item).strip() for item in configured_value if str(item).strip()]


def sync_monitored_ips_from_env():
    """
    Make the DB match .env: create rows for new URLs, remove rows for URLs
    no longer configured. Never touches scheduling/active state on rows
    that already exist — that would clobber the dispatch loop.
    """
    configured_urls = get_monitored_ips_from_env()
    existing_urls = set(UptimeIP.objects.values_list('url', flat=True))
    interval = int(getattr(settings, 'CHECK_INTERVAL_SECONDS', 30))
    timeout = int(getattr(settings, 'CHECK_TIMEOUT_SECONDS', 10))

    configured = set()
    for url in configured_urls:
        if url in configured:
            continue
        configured.add(url)

        if url not in existing_urls:
            UptimeIP.objects.create(
                url=url,
                name=url,
                check_interval_seconds=interval,
                timeout_seconds=timeout,
                next_check_at=timezone.now(),
            )

    removed_urls = existing_urls - configured
    if removed_urls:
        UptimeIP.objects.filter(url__in=removed_urls).delete()

    return list(configured)


@shared_task(name='uptime.tasks.dispatch_due_checks')
def dispatch_due_checks():
    """Check all configured IPs on a single global interval."""
    sync_monitored_ips_from_env()
    now = timezone.now()

    due = list(
        UptimeIP.objects.filter(is_active=True, next_check_at__lte=now)
        .values_list('id', 'check_interval_seconds')
    )
    for ip_id, ip_interval in due:
        UptimeIP.objects.filter(pk=ip_id).update(
            next_check_at=now + timezone.timedelta(seconds=ip_interval)
        )
        check_ip.delay(ip_id)
    return len(due)


@shared_task(name='uptime.tasks.check_ip')
def check_ip(uptime_ip_id):
    """Perform one HTTP check against a single monitored endpoint."""
    try:
        ip_obj = UptimeIP.objects.get(pk=uptime_ip_id)
    except UptimeIP.DoesNotExist:
        logger.warning('check_ip: UptimeIP %s no longer exists', uptime_ip_id)
        return

    now = timezone.now()
    is_up = False
    status_code = None

    start = time.monotonic()
    try:
        response = requests.get(ip_obj.url, timeout=ip_obj.timeout_seconds)
        status_code = response.status_code
        is_up = 200 <= status_code < 400
    except requests.RequestException:
        is_up = False

    response_time_ms = int((time.monotonic() - start) * 1000)
    new_status = UptimeIP.STATUS_UP if is_up else UptimeIP.STATUS_DOWN
    previous_status = ip_obj.current_status
    is_first_check = ip_obj.last_status_change_at is None
    status_changed = previous_status != new_status

    # last_checked_at always moves forward — every check updates it.
    ip_obj.last_checked_at = now
    ip_obj.current_status = new_status

    # last_up_at / last_down_at / last_status_change_at only move on an
    # ACTUAL transition (or the very first real check). They mark "when
    # this status started", not "when we last confirmed it". A down IP
    # that stays down for an hour keeps its original last_down_at.
    if is_first_check or status_changed:
        ip_obj.last_status_change_at = now
        if new_status == UptimeIP.STATUS_UP:
            ip_obj.last_up_at = now
        else:
            ip_obj.last_down_at = now

    try:
        ip_obj.save(update_fields=[
            'current_status', 'last_checked_at', 'last_up_at', 'last_down_at', 'last_status_change_at'
        ])
    except DatabaseError:
        logger.warning('check_ip: UptimeIP %s was deleted mid-check, discarding result', uptime_ip_id)
        return

    return {
        'ip': ip_obj.url,
        'status': new_status,
        'status_code': status_code,
        'response_time_ms': response_time_ms,
    }