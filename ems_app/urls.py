from django.urls import path
from . import views

urlpatterns = [
    # Event listing and details
    path('', views.EventListView.as_view(), name='event-list'),
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
    path('admin/event/<int:pk>/approval/', views.event_approval, name='event-approval'),
]
