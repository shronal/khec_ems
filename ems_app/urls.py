from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ems_app.views import home

urlpatterns = [
    path('about/', views.about_us, name='about-us'),
    path('contact/', views.contact, name='contact-us'),
    # Event listing and details
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event-detail'),
    
    # Event management
    path('create/', views.EventCreateView.as_view(), name='event-create'),
    path('event/<slug:slug>/edit/', views.EventUpdateView.as_view(), name='event-update'),
    path('event/<slug:slug>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    
    # Registration
    path('event/<slug:slug>/register/', views.register_for_event, name='event-register'),
    path('event/<slug:slug>/cancel-registration/', views.cancel_registration, name='cancel-registration'),
    
    # Interaction
    path('event/<slug:slug>/feedback/', views.submit_feedback, name='submit-feedback'),
    
    # Check-in
    path('event/<slug:slug>/checkin/', views.event_checkin, name='event-checkin'),
    
    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('organizer-dashboard/', views.organizer_dashboard, name='organizer-dashboard'),
    path('my-registrations/', views.user_registrations, name='user-registrations'),
    
    # Admin functions
    path('event/<slug:slug>/approval/', views.event_approval_view, name='event-approval'),
    path("api/check_overlap/", views.check_overlap, name="check_overlap"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
