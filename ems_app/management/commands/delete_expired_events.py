# your_app/management/commands/delete_expired_events.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from ems_app.models import Event

class Command(BaseCommand):
    help = 'Deletes events whose registration deadline has passed'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        expired_events = Event.objects.filter(registration_deadline__lt=today)
        count = expired_events.count()
        expired_events.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} expired events.'))
