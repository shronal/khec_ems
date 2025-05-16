from django import forms
from .models import Event, EventRegistration, EventFeedback, EventCategory

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'location', 'start_date', 
                  'end_date', 'registration_deadline', 'max_participants', 'image']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date should be after start date.")
        
        if start_date and registration_deadline and registration_deadline > start_date:
            raise forms.ValidationError("Registration deadline should be before the event starts.")
        
        return cleaned_data

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = []  # No fields needed as we'll set event and participant in the view

class EventFeedbackForm(forms.ModelForm):
    class Meta:
        model = EventFeedback
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class EventApprovalForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['status']
