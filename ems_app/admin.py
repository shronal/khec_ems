from django.contrib import admin
from .models import (
    EventCategory, Event, EventRegistration, EventFeedback, 
    EventComment, EventShare, EventAnalytics, EventTemplate,
    EventImage, EventWaitlist, EventReminder
)

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'icon', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'color', 'icon')

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'start_date', 'status', 'view_count', 'get_registered_count')
    list_filter = ('status', 'category', 'is_featured', 'is_free', 'start_date', 'created_at')
    search_fields = ('title', 'description', 'location', 'organizer__username')
    date_hierarchy = 'start_date'
    readonly_fields = ('slug', 'view_count', 'share_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'description', 'category', 'organizer')
        }),
        ('Location & Time', {
            'fields': ('location', 'venue_details', 'latitude', 'longitude', 'start_date', 'end_date', 'registration_deadline')
        }),
        ('Registration', {
            'fields': ('max_participants', 'min_participants', 'registration_fee', 'is_free')
        }),
        ('Event Details', {
            'fields': ('requirements', 'agenda', 'contact_email', 'contact_phone')
        }),
        ('Media', {
            'fields': ('featured_image', 'banner_image')
        }),
        ('Status & Settings', {
            'fields': ('status', 'priority', 'is_featured', 'is_recurring')
        }),
        ('Analytics', {
            'fields': ('view_count', 'share_count'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_registered_count(self, obj):
        return obj.get_registered_count()
    get_registered_count.short_description = 'Registrations'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'participant', 'status', 'registration_date', 'checked_in')
    list_filter = ('status', 'checked_in', 'registration_date', 'event__category')
    search_fields = ('event__title', 'participant__username', 'participant__email')
    date_hierarchy = 'registration_date'
    readonly_fields = ('registration_date', 'check_in_time')
    
    fieldsets = (
        ('Registration Info', {
            'fields': ('event', 'participant', 'status', 'registration_date')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'check_in_time', 'checked_in_by')
        }),
        ('Additional Info', {
            'fields': ('notes', 'emergency_contact', 'dietary_requirements')
        }),
        ('Notifications', {
            'fields': ('email_sent', 'reminder_sent'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at', 'event__category')
    search_fields = ('event__title', 'user__username', 'comment')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'content_preview', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('event__title', 'user__username', 'content')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_by', 'is_public', 'created_at')
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')

@admin.register(EventAnalytics)
class EventAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('event', 'total_views', 'confirmed_registrations', 'average_rating', 'attendance_rate', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('event__title',)
    readonly_fields = ('last_updated',)

@admin.register(EventShare)
class EventShareAdmin(admin.ModelAdmin):
    list_display = ('event', 'platform', 'user', 'shared_at')
    list_filter = ('platform', 'shared_at')
    search_fields = ('event__title', 'user__username')
    date_hierarchy = 'shared_at'

@admin.register(EventWaitlist)
class EventWaitlistAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'position', 'joined_at', 'notified')
    list_filter = ('notified', 'joined_at')
    search_fields = ('event__title', 'user__username')
    ordering = ('event', 'position')

@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'reminder_type', 'send_time', 'is_sent', 'recipients_count')
    list_filter = ('reminder_type', 'is_sent', 'send_time')
    search_fields = ('event__title',)
    date_hierarchy = 'send_time'
