from django.urls import path
from . import views
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ems_app.views import home

from django.urls import path
from .views import approve_event, reject_event

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
    path('event/<slug:slug>/approval/', views.event_approval, name='event-approval'),


    path('event/<int:event_id>/approve/', approve_event, name='approve_event'),
    path('event/<int:event_id>/reject/', reject_event, name='reject_event'),

     
    # path('event/<int:event_id>/esewa/', views.esewa_payment, name='esewa_payment'),
    # path('event/esewa-success/', views.esewa_success, name='esewa_success'),



    path('event/<slug:slug>/register/', views.event_register, name='event-register'),
    path('event/<slug:slug>/esewa/payment/', views.show_payment, name='show_payment'),
    path('event/<slug:slug>/esewa/success/', views.esewa_success, name='esewa-success'),
    path('event/<slug:slug>/esewa/cancel/', views.property_cancel, name='esewa-cancel'),


    path("api/check_overlap/", views.check_overlap, name="check_overlap"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



   
    


    


