from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm, UserUpdateForm, SimpleLoginForm
from .models import CustomUser

def custom_login(request):
    """
    Simple custom login view
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SimpleLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Try to authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(
                        request, 
                        f'Welcome back, {user.get_full_name() or user.username}!'
                    )
                    
                    # Redirect based on user type
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    elif user.is_admin_user():
                        return redirect('admin-dashboard')
                    elif user.is_organizer():
                        return redirect('organizer-dashboard')
                    else:
                        return redirect('user-dashboard')
                else:
                    messages.error(request, 'Your account has been deactivated.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    else:
        form = SimpleLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request, 
                f'Account created successfully for {username}! You can now log in.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def custom_logout(request):
    user_name = request.user.username if request.user.is_authenticated else None
    logout(request)
    
    if user_name:
        messages.success(request, f'Goodbye {user_name}! You have been logged out successfully.')
    else:
        messages.info(request, 'You have been logged out.')
    
    return redirect('home')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserUpdateForm(instance=request.user)
    
    # Get user statistics
    user_stats = {
        'total_events_organized': request.user.organized_events.count(),
        'total_registrations': request.user.event_registrations.count(),
        'approved_events': request.user.organized_events.filter(status='approved').count(),
        'pending_events': request.user.organized_events.filter(status='pending').count(),
    }
    
    context = {
        'form': form,
        'user_stats': user_stats,
    }
    return render(request, 'users/profile.html', context)

@login_required
def dashboard(request):
    """User dashboard based on user type"""
    user = request.user
    
    if user.is_admin_user():
        return redirect('admin-dashboard')
    elif user.is_organizer():
        return redirect('organizer-dashboard')
    else:
        return redirect('user-dashboard')

@login_required
def user_dashboard(request):
    """Dashboard for general users"""
    user = request.user
    
    # Get user's registered events
    registered_events = user.event_registrations.select_related('event').order_by('-registration_date')[:5]
    
    # Get upcoming events user is registered for
    from django.utils import timezone
    upcoming_events = user.event_registrations.filter(
        event__start_date__gte=timezone.now()
    ).select_related('event').order_by('event__start_date')[:5]
    
    context = {
        'registered_events': registered_events,
        'upcoming_events': upcoming_events,
        'total_registrations': user.event_registrations.count(),
    }
    
    return render(request, 'users/user_dashboard.html', context)

@login_required
def user_registrations(request):
    """View for user's event registrations"""
    from django.utils import timezone
    
    # Get all events the user is registered for
    registrations = request.user.event_registrations.select_related('event').order_by('-registration_date')
    
    context = {
        'registrations': registrations,
        'now': timezone.now(),
    }
    
    return render(request, 'events/user_registrations.html', context)

@login_required
def organizer_dashboard(request):
    """Dashboard for organizers"""
    if not (request.user.is_organizer() or request.user.is_admin_user()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    user = request.user
    
    # Get organizer's events
    events = user.organized_events.order_by('-created_at')
    
    # Event statistics
    event_stats = {
        'total_events': events.count(),
        'approved_events': events.filter(status='approved').count(),
        'pending_events': events.filter(status='pending').count(),
        'rejected_events': events.filter(status='rejected').count(),
    }
    
    # Recent events
    recent_events = events[:5]
    
    context = {
        'events': events,
        'event_stats': event_stats,
        'recent_events': recent_events,
    }
    
    return render(request, 'events/organizer_dashboard.html', context)
