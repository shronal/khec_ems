from django.contrib import admin
from .models import EventCategory, Event, EventRegistration, EventFeedback

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'category', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'participant', 'registration_date', 'attended')
    list_filter = ('attended', 'registration_date')
    search_fields = ('event__title', 'participant__username')
    date_hierarchy = 'registration_date'

@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('event__title', 'user__username', 'comment')
    date_hierarchy = 'created_at'
