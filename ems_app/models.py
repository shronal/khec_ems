from django.db import models
from django.urls import reverse
from users.models import CustomUser

class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Event Categories"

from django.utils import timezone
from django.db import models

class Event(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        'EventCategory',  # Use string reference to avoid circular imports
        on_delete=models.CASCADE, 
        related_name='events'
    )
    organizer = models.ForeignKey(
        'users.CustomUser',  # Assuming CustomUser is in users app
        on_delete=models.CASCADE,
        related_name='organized_events',
        limit_choices_to={'user_type': 'organizer'}, # Only organizers can be assigned
        null=True,
        blank=True
    )
    location = models.CharField(max_length=200)
    start_date = models.DateTimeField(
        default=timezone.now,  # Sensible default
        help_text="When the event starts"
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the event ends (optional)"
    )
    registration_deadline = models.DateTimeField(
        default=timezone.now,  # Default to now
        help_text="Last date to register"
    )
    max_participants = models.PositiveIntegerField(
        default=0,
        help_text="0 means unlimited"
    )
    image = models.ImageField(
        upload_to='event_images/%Y/%m/%d/',  # Better file organization
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']  # Default ordering
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def is_registration_open(self):
        return timezone.now() < self.registration_deadline

    @property
    def duration(self):
        if self.end_date:
            return self.end_date - self.start_date
        return None
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event-detail', kwargs={'pk': self.pk})
    
    def is_registration_open(self):
        from django.utils import timezone
        return self.status == 'approved' and self.registration_deadline > timezone.now()
    
    def get_registered_count(self):
        return self.registrations.count()
    
    def has_spots_left(self):
        if self.max_participants == 0:  # Unlimited
            return True
        return self.get_registered_count() < self.max_participants

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'participant')
    
    def __str__(self):
        return f"{self.participant.username} - {self.event.title}"

class EventFeedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_feedback')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.rating}"


