from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
import json
import csv
from datetime import datetime, timedelta
from calendar import monthrange

from .models import (
    Event, EventRegistration, EventFeedback, EventCategory, 
    EventComment, EventShare, EventAnalytics, EventTemplate,
    EventImage, EventWaitlist
)
from .forms import (
    EventForm, EventRegistrationForm, EventFeedbackForm, 
    EventApprovalForm, EventSearchForm, EventCommentForm,
    EventTemplateForm, BulkActionForm, CheckInForm, EventExportForm
)
from users.models import CustomUser

def home(request):
    """Enhanced home view with better analytics"""
    now = timezone.now()
    
    # Featured events
    featured_events = Event.objects.filter(
        status='approved',
        is_featured=True,
        start_date__gte=now
    ).order_by('start_date')[:3]
    
    # Upcoming events
    upcoming_events = Event.objects.filter(
        status='approved',
        start_date__gte=now
    ).order_by('start_date')[:6]
    
    # Popular events (by registration count)
    popular_events = Event.objects.filter(
        status='approved',
        start_date__gte=now
    ).annotate(
        registration_count=Count('registrations')
    ).order_by('-registration_count')[:4]
    
    # Event categories with counts
    categories = EventCategory.objects.filter(
        is_active=True
    ).annotate(
        event_count=Count('events', filter=Q(events__status='approved'))
    ).order_by('-event_count')[:6]
    
    # Statistics
    stats = {
        'total_events': Event.objects.filter(status='approved').count(),
        'upcoming_events': Event.objects.filter(status='approved', start_date__gte=now).count(),
        'total_registrations': EventRegistration.objects.filter(status='confirmed').count(),
        'active_organizers': CustomUser.objects.filter(
            organized_events__status='approved'
        ).distinct().count(),
    }
    
    context = {
        'featured_events': featured_events,
        'upcoming_events': upcoming_events,
        'popular_events': popular_events,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'events/home.html', context)


def about_us(request):
    """About Us page view"""
    context = {
        'page_title': 'About Us - KhEC Event Flow',
    }
    return render(request, 'events/about_us.html', context)

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='approved').select_related('category', 'organizer')
        
        # Get search parameters
        query = self.request.GET.get('q', '')
        category = self.request.GET.get('category', '')
        date_filter = self.request.GET.get('date_filter', 'upcoming')
        sort_by = self.request.GET.get('sort_by', 'start_date')
        is_free = self.request.GET.get('is_free', '')
        has_spots = self.request.GET.get('has_spots', '')
        
        # Apply search query
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(short_description__icontains=query)
            )
        
        # Apply category filter
        if category:
            try:
                category_obj = EventCategory.objects.get(id=category)
                queryset = queryset.filter(category=category_obj)
            except (EventCategory.DoesNotExist, ValueError):
                pass
        
        # Apply date filter
        now = timezone.now()
        if date_filter == 'upcoming':
            queryset = queryset.filter(start_date__gte=now)
        elif date_filter == 'this_week':
            week_start = now.date()
            week_end = week_start + timedelta(days=7)
            queryset = queryset.filter(start_date__date__range=[week_start, week_end])
        elif date_filter == 'this_month':
            month_start = now.replace(day=1).date()
            _, last_day = monthrange(now.year, now.month)
            month_end = now.replace(day=last_day).date()
            queryset = queryset.filter(start_date__date__range=[month_start, month_end])
        elif date_filter == 'past':
            queryset = queryset.filter(end_date__lt=now)
        
        # Apply free events filter
        if is_free:
            queryset = queryset.filter(is_free=True)
        
        # Apply available spots filter
        if has_spots:
            queryset = queryset.filter(
                Q(max_participants=0) |  # Unlimited
                Q(max_participants__gt=Count('registrations', filter=Q(registrations__status='confirmed')))
            )
        
        # Apply sorting
        if sort_by in ['start_date', '-start_date', 'title', '-title', '-created_at', 'registration_deadline', '-view_count']:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('start_date')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add search form data
        context['query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['date_filter'] = self.request.GET.get('date_filter', 'upcoming')
        context['sort_by'] = self.request.GET.get('sort_by', 'start_date')
        context['is_free'] = self.request.GET.get('is_free', '')
        context['has_spots'] = self.request.GET.get('has_spots', '')
        
        # Add categories for filter dropdown
        context['categories'] = EventCategory.objects.filter(is_active=True).order_by('name')
        
        # Add filter counts
        now = timezone.now()
        context['filter_counts'] = {
            'total': Event.objects.filter(status='approved').count(),
            'upcoming': Event.objects.filter(status='approved', start_date__gte=now).count(),
            'free': Event.objects.filter(status='approved', is_free=True).count(),
        }
        
        return context

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Increment view count
        Event.objects.filter(pk=obj.pk).update(view_count=F('view_count') + 1)
        
        # Update analytics if exists
        try:
            analytics = EventAnalytics.objects.get(event=obj)
            EventAnalytics.objects.filter(pk=analytics.pk).update(total_views=F('total_views') + 1)
        except EventAnalytics.DoesNotExist:
            EventAnalytics.objects.create(event=obj, total_views=1)
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user
        now = timezone.now()
        
        # Registration status
        is_registered = False
        registration = None
        can_register = False
        is_waitlisted = False
        
        if user.is_authenticated:
            try:
                registration = EventRegistration.objects.get(event=event, participant=user)
                is_registered = True
            except EventRegistration.DoesNotExist:
                pass
            
            # Check waitlist
            try:
                EventWaitlist.objects.get(event=event, user=user)
                is_waitlisted = True
            except EventWaitlist.DoesNotExist:
                pass
            
            # Can register check
            can_register = (
                not is_registered and
                not is_waitlisted and
                event.status == 'approved' and
                event.is_registration_open() and
                (event.has_spots_left() or event.max_participants == 0)
            )
        
        context.update({
            'is_registered': is_registered,
            'registration': registration,
            'can_register': can_register,
            'is_waitlisted': is_waitlisted,
            'now': now,
        })
        
        # Comments
        context['comments'] = event.comments.filter(
            is_approved=True, 
            parent=None
        ).select_related('user').prefetch_related('replies')[:10]
        
        # Feedback
        context['feedback_list'] = event.feedback.filter(
            is_approved=True
        ).select_related('user').order_by('-created_at')[:10]
        
        # Similar events
        context['similar_events'] = Event.objects.filter(
            category=event.category,
            status='approved',
            start_date__gte=now
        ).exclude(id=event.id)[:4]
        
        # Event images
        context['event_images'] = event.images.all().order_by('-is_featured', '-uploaded_at')[:6]
        
        # Analytics for organizer/admin
        if user.is_authenticated and (user == event.organizer or user.is_admin_user()):
            analytics, created = EventAnalytics.objects.get_or_create(event=event)
            if not created:
                analytics.update_analytics()
            context['analytics'] = analytics
        
        # Forms
        context['feedback_form'] = EventFeedbackForm()
        context['comment_form'] = EventCommentForm()
        
        return context

@login_required
def user_registrations(request):
    """View for user's event registrations"""
    now = timezone.now()
    
    # Get all events the user is registered for
    registrations = EventRegistration.objects.filter(
        participant=request.user
    ).select_related('event', 'event__category').order_by('-registration_date')
    
    context = {
        'registrations': registrations,
        'now': now,
    }
    
    return render(request, 'events/user_registrations.html', context)

@login_required
def register_for_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check if registration is allowed
    if not event.is_registration_open():
        messages.error(request, 'Registration for this event is closed.')
        return redirect('event-detail', slug=event.slug)
    
    # Check if user is already registered
    if EventRegistration.objects.filter(event=event, participant=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('event-detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            # Check if there are spots left
            if event.has_spots_left() or event.max_participants == 0:
                registration = form.save(commit=False)
                registration.event = event
                registration.participant = request.user
                registration.status = 'confirmed'
                registration.save()
                
                # Update analytics
                analytics, created = EventAnalytics.objects.get_or_create(event=event)
                analytics.update_analytics()
                
                messages.success(
                    request, 
                    f'You have successfully registered for {event.title}!'
                )
            else:
                # Add to waitlist
                position = EventWaitlist.objects.filter(event=event).count() + 1
                EventWaitlist.objects.create(
                    event=event,
                    user=request.user,
                    position=position
                )
                messages.info(
                    request,
                    f'Event is full. You have been added to the waitlist at position {position}.'
                )
            
            return redirect('event-detail', slug=event.slug)
    else:
        form = EventRegistrationForm()
    
    return render(request, 'events/event_register.html', {
        'event': event,
        'form': form
    })

@login_required
def cancel_registration(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    try:
        registration = EventRegistration.objects.get(
            event=event, 
            participant=request.user
        )
    except EventRegistration.DoesNotExist:
        messages.error(request, 'You are not registered for this event.')
        return redirect('event-detail', slug=event.slug)
    
    # Only allow cancellation if event hasn't started yet
    if event.start_date <= timezone.now():
        messages.error(
            request, 
            'You cannot cancel registration for an event that has already started.'
        )
        return redirect('event-detail', slug=event.slug)
    
    registration.status = 'cancelled'
    registration.save()
    
    # Check waitlist and promote next person
    waitlist_entry = EventWaitlist.objects.filter(event=event).first()
    if waitlist_entry:
        # Create registration for waitlisted user
        EventRegistration.objects.create(
            event=event,
            participant=waitlist_entry.user,
            status='confirmed'
        )
        
        # Remove from waitlist
        waitlist_entry.delete()
        
        # Update positions for remaining waitlist
        remaining_waitlist = EventWaitlist.objects.filter(event=event).order_by('position')
        for i, entry in enumerate(remaining_waitlist, 1):
            entry.position = i
            entry.save()
    
    # Update analytics
    analytics, created = EventAnalytics.objects.get_or_create(event=event)
    analytics.update_analytics()
    
    messages.success(
        request, 
        f'Your registration for {event.title} has been cancelled.'
    )
    return redirect('event-detail', slug=event.slug)

@login_required
def submit_feedback(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user is registered for the event
    if not EventRegistration.objects.filter(
        event=event, 
        participant=request.user,
        status='confirmed'
    ).exists():
        messages.error(
            request, 
            'You can only provide feedback for events you have registered for.'
        )
        return redirect('event-detail', slug=event.slug)
    
    # Check if event has ended
    if event.end_date > timezone.now():
        messages.error(
            request, 
            'You can only provide feedback after the event has ended.'
        )
        return redirect('event-detail', slug=event.slug)
    
    # Check if user has already submitted feedback
    if EventFeedback.objects.filter(event=event, user=request.user).exists():
        messages.error(
            request, 
            'You have already submitted feedback for this event.'
        )
        return redirect('event-detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.event = event
            feedback.user = request.user
            feedback.save()
            
            # Update analytics
            analytics, created = EventAnalytics.objects.get_or_create(event=event)
            analytics.update_analytics()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('event-detail', slug=event.slug)
    
    return redirect('event-detail', slug=event.slug)

# Additional views for completeness
class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        return self.request.user.is_organizer() or self.request.user.is_admin_user()
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        
        # Set status based on user type
        if self.request.user.is_admin_user():
            form.instance.status = 'approved'
            form.instance.approved_at = timezone.now()
        else:
            form.instance.status = 'pending'
        
        response = super().form_valid(form)
        
        # Create analytics record
        EventAnalytics.objects.create(event=self.object)
        
        messages.success(
            self.request, 
            'Your event has been created successfully! ' + 
            ('It is now live.' if form.instance.status == 'approved' else 'It will be reviewed by administrators.')
        )
        return response

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        event = self.get_object()
        return (
            self.request.user == event.organizer or 
            self.request.user.is_admin_user()
        )

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event-list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        event = self.get_object()
        return (
            self.request.user == event.organizer or 
            self.request.user.is_admin_user()
        )

@login_required
def admin_dashboard(request):
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    pending_events = Event.objects.filter(status='pending').order_by('created_at')
    approved_events = Event.objects.filter(status='approved').order_by('-start_date')
    rejected_events = Event.objects.filter(status='rejected').order_by('-updated_at')
    
    context = {
        'pending_events': pending_events,
        'approved_events': approved_events,
        'rejected_events': rejected_events,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def event_approval(request, slug):
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    event = get_object_or_404(Event, slug=slug)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['approved', 'rejected']:
            event.status = status
            if status == 'approved':
                event.approved_at = timezone.now()
            event.save()
            
            if status == 'approved':
                messages.success(request, f'Event "{event.title}" has been approved.')
            else:
                messages.success(request, f'Event "{event.title}" has been rejected.')
            
            return redirect('admin-dashboard')
    
    context = {
        'event': event,
    }
    
    return render(request, 'admin/event_approval.html', context)

@login_required
def organizer_dashboard(request):
    if not request.user.is_organizer() and not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all events organized by the user
    events = Event.objects.filter(organizer=request.user).order_by('-created_at')
    
    context = {
        'recent_events': events, 
    }
    
    return render(request, 'events/organizer_dashboard.html', context)

@login_required
def event_checkin(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Only organizer or admin can check in participants
    if not (request.user == event.organizer or request.user.is_admin_user()):
        messages.error(request, 'You do not have permission to check in participants.')
        return redirect('event-detail', slug=event.slug)
    
    if request.method == 'POST':
        participant_username = request.POST.get('participant_username')
        if participant_username:
            try:
                participant = CustomUser.objects.get(username=participant_username)
                registration = EventRegistration.objects.get(
                    event=event,
                    participant=participant,
                    status='confirmed'
                )
                
                if registration.checked_in:
                    messages.warning(
                        request, 
                        f'{participant.get_full_name() or participant.username} is already checked in.'
                    )
                else:
                    registration.checked_in = True
                    registration.check_in_time = timezone.now()
                    registration.checked_in_by = request.user
                    registration.save()
                    
                    # Update analytics
                    analytics, created = EventAnalytics.objects.get_or_create(event=event)
                    analytics.update_analytics()
                    
                    messages.success(
                        request,
                        f'{participant.get_full_name() or participant.username} has been checked in successfully!'
                    )
                
            except (CustomUser.DoesNotExist, EventRegistration.DoesNotExist):
                messages.error(request, 'Participant not found or not registered.')
    
    # Get registration statistics
    registrations = event.registrations.filter(status='confirmed')
    checked_in_count = registrations.filter(checked_in=True).count()
    total_registered = registrations.count()
    
    context = {
        'event': event,
        'registrations': registrations.order_by('participant__first_name'),
        'checked_in_count': checked_in_count,
        'total_registered': total_registered,
        'attendance_rate': (checked_in_count / total_registered * 100) if total_registered > 0 else 0,
    }
    
    return render(request, 'events/event_checkin.html', context)


# views.py
from django.http import JsonResponse
from .models import Event, EventLocation
from django.utils.dateparse import parse_datetime

def check_overlap(request):
    location_id = request.GET.get("location_id")
    start = parse_datetime(request.GET.get("start_date"))
    end = parse_datetime(request.GET.get("end_date"))

    overlap = Event.objects.filter(
        location_id=location_id,
        start_date__lt=end,
        end_date__gt=start
    ).exists()

    return JsonResponse({"overlap": overlap})
