from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def home(request):
    # In a real application, you would fetch these from your database
    # This is just example data for demonstration
    
    upcoming_events = [
        {
            'id': 1,
            'title': 'Tech Conference 2025',
            'date': 'May 15-17, 2025',
            'location': 'San Francisco, CA',
            'image': {
                'url': 'https://via.placeholder.com/500x300'
            },
            'attendees': '1,200',
            'category': 'Technology',
        },
        {
            'id': 2,
            'title': 'Music Festival',
            'date': 'June 10-12, 2025',
            'location': 'Austin, TX',
            'image': {
                'url': 'https://via.placeholder.com/500x300'
            },
            'attendees': '5,000',
            'category': 'Entertainment',
        },
        {
            'id': 3,
            'title': 'Business Summit',
            'date': 'July 22-23, 2025',
            'location': 'New York, NY',
            'image': {
                'url': 'https://via.placeholder.com/500x300'
            },
            'attendees': '800',
            'category': 'Business',
        },
    ]
    
    testimonials = [
        {
            'id': 1,
            'name': 'Sarah Johnson',
            'role': 'Event Director',
            'company': 'TechCorp',
            'content': 'EventFlow transformed how we manage our annual conference. The platform is intuitive and the support team is exceptional!',
            'avatar': {
                'url': 'https://via.placeholder.com/100'
            },
        },
        {
            'id': 2,
            'name': 'Michael Chen',
            'role': 'Marketing Manager',
            'company': 'Global Events',
            'content': 'We\'ve increased our event attendance by 40% since using EventFlow. The analytics and marketing tools are game-changers.',
            'avatar': {
                'url': 'https://via.placeholder.com/100'
            },
        },
        {
            'id': 3,
            'name': 'Jessica Williams',
            'role': 'CEO',
            'company': 'Summit Productions',
            'content': 'From small workshops to our flagship conference with 5,000+ attendees, EventFlow scales perfectly for all our needs.',
            'avatar': {
                'url': 'https://via.placeholder.com/100'
            },
        },
    ]
    
    context = {
        'upcoming_events': upcoming_events,
        'testimonials': testimonials,
    }
    
    return render(request, 'home.html', context)

@login_required
def dashboard(request):
    # Dashboard view logic here
    return render(request, 'dashboard.html')

def events(request):
    # Events view logic here
    return render(request, 'events.html')

def event_detail(request, event_id):
    # Event detail view logic here
    return render(request, 'event_detail.html')

def features(request):
    # Features view logic here
    return render(request, 'features.html')

def pricing(request):
    # Pricing view logic here
    return render(request, 'pricing.html')

def resources(request):
    # Resources view logic here
    return render(request, 'resources.html')

def demo(request):
    # Demo view logic here
    return render(request, 'demo.html')

def terms(request):
    # Terms view logic here
    return render(request, 'terms.html')

def privacy(request):
    # Privacy view logic here
    return render(request, 'privacy.html')

def password_reset(request):
    # Password reset view logic here
    return render(request, 'password_reset.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q
from .models import Event, EventRegistration, EventFeedback, EventCategory
from .forms import EventForm, EventRegistrationForm, EventFeedbackForm, EventApprovalForm
from users.models import CustomUser

def home(request):
    upcoming_events = Event.objects.filter(
        status='approved',
        start_date__gte=timezone.now()
    ).order_by('start_date')[:5]
    
    context = {
        'upcoming_events': upcoming_events,
    }
    return render(request, 'events/home.html', context)

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='approved')
        
        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
        
        # Filter by search query if provided
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )
        
        # Filter by date range
        date_filter = self.request.GET.get('date_filter', 'upcoming')
        if date_filter == 'upcoming':
            queryset = queryset.filter(start_date__gte=timezone.now())
        elif date_filter == 'past':
            queryset = queryset.filter(end_date__lt=timezone.now())
        
        return queryset.order_by('start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EventCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        context['query'] = self.request.GET.get('q', '')
        context['date_filter'] = self.request.GET.get('date_filter', 'upcoming')
        return context

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Check if user is registered
        is_registered = False
        can_register = False
        
        if self.request.user.is_authenticated:
            is_registered = EventRegistration.objects.filter(
                event=event, 
                participant=self.request.user
            ).exists()
            
            # User can register if:
            # 1. Event is approved
            # 2. Registration is still open
            # 3. There are spots left
            # 4. User is not already registered
            can_register = (
                event.status == 'approved' and
                event.is_registration_open() and
                event.has_spots_left() and
                not is_registered
            )
        
        context['is_registered'] = is_registered
        context['can_register'] = can_register
        
        # Add feedback form if user is registered and event has ended
        if is_registered and event.end_date < timezone.now():
            # Check if user has already given feedback
            has_feedback = EventFeedback.objects.filter(
                event=event,
                user=self.request.user
            ).exists()
            
            if not has_feedback:
                context['feedback_form'] = EventFeedbackForm()
        
        # Get event feedback
        context['feedback'] = event.feedback.all().order_by('-created_at')
        
        return context

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        return self.request.user.is_organizer() or self.request.user.is_admin_user()
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, 'Your event has been submitted for approval!')
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        event = self.get_object()
        return (
            self.request.user == event.organizer or 
            self.request.user.is_admin_user()
        )
    
    def form_valid(self, form):
        # If an organizer updates an approved event, set it back to pending
        if (
            self.request.user == self.get_object().organizer and 
            self.get_object().status == 'approved' and
            not self.request.user.is_admin_user()
        ):
            form.instance.status = 'pending'
            messages.info(self.request, 'Your event has been updated and will need to be re-approved.')
        else:
            messages.success(self.request, 'Event has been updated successfully!')
        
        return super().form_valid(form)

class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event-list')
    
    def test_func(self):
        event = self.get_object()
        return (
            self.request.user == event.organizer or 
            self.request.user.is_admin_user()
        )
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Event has been deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    # Check if registration is allowed
    if not event.is_registration_open():
        messages.error(request, 'Registration for this event is closed.')
        return redirect('event-detail', pk=event.pk)
    
    # Check if there are spots left
    if not event.has_spots_left():
        messages.error(request, 'This event is already at full capacity.')
        return redirect('event-detail', pk=event.pk)
    
    # Check if user is already registered
    if EventRegistration.objects.filter(event=event, participant=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('event-detail', pk=event.pk)
    
    # Create registration
    registration = EventRegistration(event=event, participant=request.user)
    registration.save()
    
    messages.success(request, f'You have successfully registered for {event.title}!')
    return redirect('event-detail', pk=event.pk)

@login_required
def cancel_registration(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(EventRegistration, event=event, participant=request.user)
    
    # Only allow cancellation if event hasn't started yet
    if event.start_date <= timezone.now():
        messages.error(request, 'You cannot cancel registration for an event that has already started.')
        return redirect('event-detail', pk=event.pk)
    
    registration.delete()
    messages.success(request, f'Your registration for {event.title} has been cancelled.')
    return redirect('event-detail', pk=event.pk)

@login_required
def submit_feedback(request, pk):
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user is registered for the event
    if not EventRegistration.objects.filter(event=event, participant=request.user).exists():
        messages.error(request, 'You can only provide feedback for events you have registered for.')
        return redirect('event-detail', pk=event.pk)
    
    # Check if event has ended
    if event.end_date > timezone.now():
        messages.error(request, 'You can only provide feedback after the event has ended.')
        return redirect('event-detail', pk=event.pk)
    
    # Check if user has already submitted feedback
    if EventFeedback.objects.filter(event=event, user=request.user).exists():
        messages.error(request, 'You have already submitted feedback for this event.')
        return redirect('event-detail', pk=event.pk)
    
    if request.method == 'POST':
        form = EventFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.event = event
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('event-detail', pk=event.pk)
    
    return redirect('event-detail', pk=event.pk)

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
def event_approval(request, pk):
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventApprovalForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            status = form.cleaned_data['status']
            if status == 'approved':
                messages.success(request, f'Event "{event.title}" has been approved.')
            elif status == 'rejected':
                messages.success(request, f'Event "{event.title}" has been rejected.')
            return redirect('admin-dashboard')
    else:
        form = EventApprovalForm(instance=event)
    
    context = {
        'form': form,
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
        'events': events,
    }
    
    return render(request, 'events/organizer_dashboard.html', context)

@login_required
def user_registrations(request):
    # Get all events the user is registered for
    registrations = EventRegistration.objects.filter(participant=request.user).order_by('-registration_date')
    
    context = {
        'registrations': registrations,
    }
    
    return render(request, 'events/user_registrations.html', context)
