from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Event, EventRegistration, EventFeedback, EventCategory, 
    EventTemplate, EventComment, EventImage
)

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'short_description', 'description', 'category', 
            'location', 'venue_details', 'latitude', 'longitude',
            'start_date', 'end_date', 'registration_deadline', 
            'max_participants', 'min_participants', 'registration_fee', 'is_free',
            'requirements', 'agenda', 'contact_email', 'contact_phone',
            'featured_image', 'banner_image', 'priority', 'is_featured',
            'meta_description', 'meta_keywords'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'venue_details': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'agenda': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'registration_fee': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['featured_image', 'banner_image', 'is_free', 'is_featured']:
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        min_participants = cleaned_data.get('min_participants')
        max_participants = cleaned_data.get('max_participants')
        
        # Date validations
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")
            
            if start_date <= timezone.now():
                raise ValidationError("Start date must be in the future.")
        
        if registration_deadline and start_date:
            if registration_deadline >= start_date:
                raise ValidationError("Registration deadline must be before the event starts.")
            
            if registration_deadline <= timezone.now():
                raise ValidationError("Registration deadline must be in the future.")
        
        # Participant validations
        if min_participants and max_participants:
            if max_participants > 0 and min_participants > max_participants:
                raise ValidationError("Minimum participants cannot exceed maximum participants.")
        
        return cleaned_data

class EventSearchForm(forms.Form):
    SORT_CHOICES = (
        ('start_date', 'Date (Earliest First)'),
        ('-start_date', 'Date (Latest First)'),
        ('title', 'Title (A-Z)'),
        ('-title', 'Title (Z-A)'),
        ('-created_at', 'Recently Added'),
        ('registration_deadline', 'Registration Deadline'),
        ('-view_count', 'Most Popular'),
    )
    
    DATE_FILTER_CHOICES = (
        ('all', 'All Events'),
        ('upcoming', 'Upcoming Events'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('past', 'Past Events'),
    )
    
    q = forms.CharField(
        max_length=255, 
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search events...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_filter = forms.ChoiceField(
        choices=DATE_FILTER_CHOICES,
        required=False,
        initial='upcoming',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='start_date',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_free = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_spots = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['notes', 'emergency_contact', 'dietary_requirements']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'dietary_requirements': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EventFeedbackForm(forms.ModelForm):
    class Meta:
        model = EventFeedback
        fields = [
            'rating', 'comment', 'organization_rating', 
            'content_rating', 'venue_rating', 'is_anonymous'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'organization_rating': forms.Select(attrs={'class': 'form-select'}),
            'content_rating': forms.Select(attrs={'class': 'form-select'}),
            'venue_rating': forms.Select(attrs={'class': 'form-select'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EventCommentForm(forms.ModelForm):
    class Meta:
        model = EventComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Share your thoughts about this event...'
            })
        }

class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = [
            'name', 'description', 'category', 'duration_hours', 
            'max_participants', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_public']:
                field.widget.attrs['class'] = 'form-control'

class EventApprovalForm(forms.ModelForm):
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'class': 'form-control',
            'placeholder': 'Reason for rejection (optional)'
        })
    )
    
    class Meta:
        model = Event
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

class BulkActionForm(forms.Form):
    ACTION_CHOICES = (
        ('approve', 'Approve Selected'),
        ('reject', 'Reject Selected'),
        ('delete', 'Delete Selected'),
        ('export', 'Export Selected'),
    )
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    selected_events = forms.CharField(widget=forms.HiddenInput())

class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ['image', 'caption', 'is_featured']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CheckInForm(forms.Form):
    participant_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter participant username'
        })
    )
    
    def __init__(self, event, *args, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)
    
    def clean_participant_username(self):
        username = self.cleaned_data['participant_username']
        try:
            from users.models import CustomUser
            user = CustomUser.objects.get(username=username)
            registration = EventRegistration.objects.get(
                event=self.event, 
                participant=user, 
                status='confirmed'
            )
            return user
        except (CustomUser.DoesNotExist, EventRegistration.DoesNotExist):
            raise ValidationError("Participant not found or not registered for this event.")

class EventExportForm(forms.Form):
    FORMAT_CHOICES = (
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    )
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_registrations = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_feedback = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
