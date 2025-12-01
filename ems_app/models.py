from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from django.contrib.auth.models import User
import uuid
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    icon = models.CharField(max_length=50, default='fas fa-calendar', help_text='FontAwesome icon class')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ['name']

class EventLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., Hall1, Hall2
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Event Locations"
        ordering = ['name']

class EventTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    duration_hours = models.PositiveIntegerField(default=2)
    max_participants = models.PositiveIntegerField(default=50)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey('EventCategory', on_delete=models.CASCADE, related_name='events')
    from django.conf import settings

    organizer = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='organized_events'
)

    
    # Location and Time
    location = models.ForeignKey(EventLocation, on_delete=models.CASCADE, related_name='events')
    venue_details = models.TextField(blank=True, help_text='Additional venue information')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    # Capacity and Registration
    max_participants = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    min_participants = models.PositiveIntegerField(default=1)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=True)
    
    # Event Details
    requirements = models.TextField(blank=True, help_text='What participants need to bring/know')
    agenda = models.TextField(blank=True, help_text='Event schedule/agenda')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    
    # Status and Metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_featured = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['category', 'start_date']),
            models.Index(fields=['organizer', '-created_at']),
        ]

    def __str__(self):
        return self.title

    # Validation to prevent overlapping events at the same location
    def clean(self):
        overlapping = Event.objects.filter(
            location=self.location,
            end_date__gte=self.start_date,
            start_date__lte=self.end_date
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                f"{self.location} is already booked between {self.start_date} and {self.end_date}."
            )

    # Save method with slug, short description, and validation
    def save(self, *args, **kwargs):
        self.full_clean()  # triggers clean() for clash prevention

        # Generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Set short description if not provided
        if not self.short_description:
            self.short_description = self.description[:297] + "..." if len(self.description) > 300 else self.description

        super().save(*args, **kwargs)

    # Utility methods
    def get_absolute_url(self):
        return reverse('event-detail', kwargs={'slug': self.slug})
    
    def is_registration_open(self):
        now = timezone.now()
        return (
            self.status == 'approved' and 
            self.registration_deadline > now and 
            self.start_date > now
        )
    
    def get_registered_count(self):
        return self.registrations.filter(status='confirmed').count()
    
    def has_spots_left(self):
        if self.max_participants == 0:  # Unlimited
            return True
        return self.get_registered_count() < self.max_participants
    
    def get_availability_percentage(self):
        if self.max_participants == 0:
            return 0
        return (self.get_registered_count() / self.max_participants) * 100
    
    def is_past_event(self):
        return self.end_date < timezone.now()
    
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def get_duration(self):
        duration = self.end_date - self.start_date
        hours = duration.total_seconds() / 3600
        return f"{hours:.1f} hours"
    
    def get_days_until_event(self):
        if self.start_date > timezone.now():
            delta = self.start_date - timezone.now()
            return delta.days
        return 0
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['category', 'start_date']),
            models.Index(fields=['organizer', '-created_at']),
        ]

class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='event_gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event.title} - Image {self.id}"
    
    class Meta:
        ordering = ['-is_featured', '-uploaded_at']

class EventRegistration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('waitlist', 'Waitlist'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='confirmed')
    
    # Check-in information
    checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(blank=True, null=True)
    checked_in_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name='checked_in_participants')
    
    # Additional information
    notes = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    dietary_requirements = models.CharField(max_length=200, blank=True)
    
    # Notifications
    email_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'participant')
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.participant.username} - {self.event.title}"

class EventFeedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_feedback')
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    
    # Detailed ratings
    organization_rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    content_rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    venue_rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    
    # Feedback metadata
    is_anonymous = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.rating}★"
    
    def get_average_detailed_rating(self):
        return (self.organization_rating + self.content_rating + self.venue_rating) / 3

class EventComment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"

class EventShare(models.Model):
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    shared_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.event.title} shared on {self.platform}"

class EventAnalytics(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='analytics')
    
    # View analytics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    
    # Registration analytics
    total_registrations = models.PositiveIntegerField(default=0)
    confirmed_registrations = models.PositiveIntegerField(default=0)
    cancelled_registrations = models.PositiveIntegerField(default=0)
    waitlist_registrations = models.PositiveIntegerField(default=0)
    
    # Engagement analytics
    total_shares = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Attendance analytics
    checked_in_count = models.PositiveIntegerField(default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def update_analytics(self):
        """Update all analytics for this event"""
        event = self.event
        
        # Registration analytics
        registrations = event.registrations.all()
        self.total_registrations = registrations.count()
        self.confirmed_registrations = registrations.filter(status='confirmed').count()
        self.cancelled_registrations = registrations.filter(status='cancelled').count()
        self.waitlist_registrations = registrations.filter(status='waitlist').count()
        
        # Engagement analytics
        self.total_shares = event.shares.count()
        self.total_comments = event.comments.filter(is_approved=True).count()
        
        # Rating analytics
        feedback = event.feedback.all()
        if feedback.exists():
            self.average_rating = sum(f.rating for f in feedback) / feedback.count()
        
        # Attendance analytics
        self.checked_in_count = registrations.filter(checked_in=True).count()
        if self.confirmed_registrations > 0:
            self.attendance_rate = (self.checked_in_count / self.confirmed_registrations) * 100
        
        self.save()
    
    def __str__(self):
        return f"Analytics for {self.event.title}"

class EventReminder(models.Model):
    REMINDER_TYPES = (
        ('registration_deadline', 'Registration Deadline'),
        ('event_start', 'Event Start'),
        ('event_end', 'Event End'),
        ('feedback_request', 'Feedback Request'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=25, choices=REMINDER_TYPES)
    send_time = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    recipients_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.reminder_type} reminder for {self.event.title}"
    
    class Meta:
        ordering = ['send_time']

class EventWaitlist(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='waitlist')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField()
    notified = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['position']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} (Position: {self.position})"
    


class Userprofile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    social_links = models.JSONField(blank=True, null=True, help_text='{"linkedin": "url", "twitter": "url"}')
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    token_created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username
    
    def get_profile_url(self):
        return reverse('user-profile', kwargs={'username': self.user.username})
    
    
    
    class Meta:
        verbose_name_plural = "User Profiles"