"""
URL configuration for ems project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('events/', views.events, name='events'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('features/', views.features, name='features'),
    path('pricing/', views.pricing, name='pricing'),
    path('resources/', views.resources, name='resources'),
    # path('demo/', views.demo, name='demo'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.EventListView.as_view(), name='event-list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('new/', views.EventCreateView.as_view(), name='event-create'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='event-update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    path('<int:pk>/register/', views.register_for_event, name='event-register'),
    path('<int:pk>/cancel-registration/', views.cancel_registration, name='cancel-registration'),
    path('<int:pk>/feedback/', views.submit_feedback, name='submit-feedback'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/event/<int:pk>/approval/', views.event_approval, name='event-approval'),
    path('organizer-dashboard/', views.organizer_dashboard, name='organizer-dashboard'),
    path('user-registrations/', views.user_registrations, name='user-registrations'),
]
