from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EventCategory, EventTemplate, Event, EventImage, EventRegistration,
    EventFeedback, EventComment, EventShare, EventAnalytics,
    EventReminder, EventWaitlist
)

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'icon_display', 'event_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'name': ('name',)}
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'
    
    def icon_display(self, obj):
        return format_html('<i class="{}" style="font-size: 18px;"></i>', obj.icon)
    icon_display.short_description = 'Icon'
    
    def event_count(self, obj):
        return obj.events.count()
    event_count.short_description = 'Events'

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ['image', 'caption', 'is_featured']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'organizer', 'status', 'start_date', 
        'registration_count', 'is_featured', 'view_count'
    ]
    list_filter = [
        'status', 'category', 'is_featured', 'is_free', 'priority',
        'start_date', 'created_at'
    ]
    search_fields = ['title', 'description', 'location', 'organizer__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    inlines = [EventImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category', 'organizer')
        }),
        ('Location & Time', {
            'fields': ('location', 'venue_details', 'start_date', 'end_date', 'registration_deadline')
        }),
        ('Registration', {
            'fields': ('max_participants', 'min_participants', 'registration_fee', 'is_free')
        }),
        ('Event Details', {
            'fields': ('requirements', 'agenda', 'contact_email', 'contact_phone'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image', 'banner_image'),
            'classes': ('collapse',)
        }),
        ('Status & Metadata', {
            'fields': ('status', 'priority', 'is_featured', 'is_recurring', 'approved_at')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    
    def registration_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()
    registration_count.short_description = 'Registrations'
    
    actions = ['approve_events', 'reject_events', 'feature_events']
    
    def approve_events(self, request, queryset):
        from django.utils import timezone
        from events.views import send_event_approval_email
        updated = queryset.update(status='approved', approved_at=timezone.now())
        
        # Send approval emails to all event organizers
        for event in queryset:
            send_event_approval_email(event, is_approved=True)
        
        self.message_user(request, f'{updated} events were approved. Notification emails sent to organizers.')
    approve_events.short_description = 'Approve selected events'
    
    def reject_events(self, request, queryset):
        from events.views import send_event_approval_email
        updated = queryset.update(status='rejected')
        
        # Send rejection emails to all event organizers
        for event in queryset:
            send_event_approval_email(event, is_approved=False, rejection_reason='Event does not meet our guidelines.')
        
        self.message_user(request, f'{updated} events were rejected. Notification emails sent to organizers.')
    reject_events.short_description = 'Reject selected events'
    
    def feature_events(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} events were featured.')
    feature_events.short_description = 'Feature selected events'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'participant', 'event', 'status', 'registration_date', 
        'checked_in', 'check_in_time'
    ]
    list_filter = ['status', 'checked_in', 'registration_date', 'event__category']
    search_fields = [
        'participant__username', 'participant__email', 
        'event__title', 'notes'
    ]
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Registration Info', {
            'fields': ('event', 'participant', 'status', 'registration_date')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'check_in_time', 'checked_in_by')
        }),
        ('Additional Info', {
            'fields': ('notes', 'emergency_contact', 'dietary_requirements'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('email_sent', 'reminder_sent'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_registrations', 'check_in_participants']
    
    def confirm_registrations(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} registrations were confirmed.')
    confirm_registrations.short_description = 'Confirm selected registrations'
    
    def check_in_participants(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(checked_in=True, check_in_time=timezone.now())
        self.message_user(request, f'{updated} participants were checked in.')
    check_in_participants.short_description = 'Check in selected participants'

@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'user', 'rating', 'organization_rating', 
        'content_rating', 'venue_rating', 'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_anonymous', 'created_at']
    search_fields = ['event__title', 'user__username', 'comment']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Feedback Info', {
            'fields': ('event', 'user', 'rating', 'comment')
        }),
        ('Detailed Ratings', {
            'fields': ('organization_rating', 'content_rating', 'venue_rating')
        }),
        ('Metadata', {
            'fields': ('is_anonymous', 'is_approved', 'helpful_count')
        }),
    )
    
    actions = ['approve_feedback', 'disapprove_feedback']
    
    def approve_feedback(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} feedback entries were approved.')
    approve_feedback.short_description = 'Approve selected feedback'
    
    def disapprove_feedback(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} feedback entries were disapproved.')
    disapprove_feedback.short_description = 'Disapprove selected feedback'

@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'content_preview', 'parent', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['event__title', 'user__username', 'content']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'is_public', 'duration_hours', 'max_participants', 'created_at']
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'description', 'category', 'created_by')
        }),
        ('Default Settings', {
            'fields': ('duration_hours', 'max_participants', 'is_public')
        }),
    )

@admin.register(EventAnalytics)
class EventAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'total_views', 'total_registrations', 'confirmed_registrations',
        'attendance_rate', 'average_rating', 'last_updated'
    ]
    list_filter = ['last_updated']
    search_fields = ['event__title']
    readonly_fields = [
        'total_views', 'unique_views', 'total_registrations', 'confirmed_registrations',
        'cancelled_registrations', 'waitlist_registrations', 'total_shares',
        'total_comments', 'average_rating', 'checked_in_count', 'attendance_rate'
    ]

@admin.register(EventWaitlist)
class EventWaitlistAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'position', 'joined_at', 'notified']
    list_filter = ['notified', 'joined_at']
    search_fields = ['event__title', 'user__username']
    ordering = ['event', 'position']

@admin.register(EventShare)
class EventShareAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'platform', 'shared_at', 'ip_address']
    list_filter = ['platform', 'shared_at']
    search_fields = ['event__title', 'user__username']
    date_hierarchy = 'shared_at'

@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ['event', 'reminder_type', 'send_time', 'is_sent', 'recipients_count']
    list_filter = ['reminder_type', 'is_sent', 'send_time']
    search_fields = ['event__title']
    date_hierarchy = 'send_time'
