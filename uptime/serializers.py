from django.utils import timezone
from rest_framework import serializers
import pytz

from .models import UptimeIP

BANGLADESH_TZ = pytz.timezone('Asia/Dhaka')


def humanize_duration(seconds):
    """322 -> '5m 22s', 90065 -> '1d 1h 1m 5s'. None -> None."""
    if seconds is None:
        return None
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f'{days}d')
    if hours or days:
        parts.append(f'{hours}h')
    if minutes or hours or days:
        parts.append(f'{minutes}m')
    parts.append(f'{seconds}s')
    return ' '.join(parts)


def convert_to_bangladesh_time(dt):
    """Convert datetime to Bangladesh timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt, timezone.utc)
    return dt.astimezone(BANGLADESH_TZ)


class UptimeIPSerializer(serializers.ModelSerializer):
    current_status_duration = serializers.SerializerMethodField()
    last_checked_at = serializers.SerializerMethodField()
    last_up_at = serializers.SerializerMethodField()
    last_down_at = serializers.SerializerMethodField()
    last_status_change_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = UptimeIP
        fields = [
            'id', 'name', 'url', 'check_interval_seconds', 'timeout_seconds',
            'is_active', 'current_status',
            'last_checked_at', 'last_up_at', 'last_down_at', 'last_status_change_at',
            'current_status_duration',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'current_status', 'last_checked_at', 'last_up_at', 'last_down_at',
            'last_status_change_at', 'created_at', 'updated_at',
        ]

    def get_current_status_duration(self, obj):
        return humanize_duration(obj.current_duration_seconds)

    def get_last_checked_at(self, obj):
        return convert_to_bangladesh_time(obj.last_checked_at)

    def get_last_up_at(self, obj):
        return convert_to_bangladesh_time(obj.last_up_at)

    def get_last_down_at(self, obj):
        return convert_to_bangladesh_time(obj.last_down_at)

    def get_last_status_change_at(self, obj):
        return convert_to_bangladesh_time(obj.last_status_change_at)

    def get_created_at(self, obj):
        return convert_to_bangladesh_time(obj.created_at)

    def get_updated_at(self, obj):
        return convert_to_bangladesh_time(obj.updated_at)

    def create(self, validated_data):
        # New IPs get checked right away instead of waiting a full interval.
        instance = UptimeIP(**validated_data)
        instance.next_check_at = timezone.now()
        instance.save()
        return instance
