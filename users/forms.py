from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import CustomUser
import re

class CustomAuthenticationForm(forms.Form):
    """
    Custom authentication form that works with our CustomUser model
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True,
            'autocomplete': 'username',
        }),
        label='Username'
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
    )
    
    error_messages = {
        'invalid_login': (
            "Please enter a correct username and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': "This account is inactive.",
    }
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
    
    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
    
    def get_user(self):
        return self.user_cache

class SimpleLoginForm(forms.Form):
    """
    Simple login form without complex validation
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'required': True
        })
    )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='Required. Enter a valid email address.'
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text='Required.'
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text='Required.'
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        }),
        help_text='Optional. Format: +977-9841234567'
    )
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Choose your role in the system.'
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update field attributes
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
        
        # Update help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and cannot be entirely numeric.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
            
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValidationError("Enter a valid email address.")
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username already exists
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError("A user with this username already exists.")
            
            # Username validation
            if len(username) < 3:
                raise ValidationError("Username must be at least 3 characters long.")
            
            if not re.match(r'^[a-zA-Z0-9@.+_-]+$', username):
                raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters.")
        
        return username
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            if not re.match(r'^[a-zA-Z\s]+$', first_name):
                raise ValidationError("First name can only contain letters and spaces.")
            if len(first_name.strip()) < 2:
                raise ValidationError("First name must be at least 2 characters long.")
        return first_name.strip().title()
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            if not re.match(r'^[a-zA-Z\s]+$', last_name):
                raise ValidationError("Last name can only contain letters and spaces.")
            if len(last_name.strip()) < 2:
                raise ValidationError("Last name must be at least 2 characters long.")
        return last_name.strip().title()
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove all non-digit characters for validation
            digits_only = re.sub(r'\D', '', phone_number)
            
            # Check if it's a valid Nepali phone number
            if not re.match(r'^(\+977)?[0-9]{10}$', digits_only) and not re.match(r'^[0-9]{10}$', digits_only):
                raise ValidationError("Enter a valid phone number (10 digits).")
        
        return phone_number
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Additional password validation
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            if password1.isdigit():
                raise ValidationError("Password cannot be entirely numeric.")
            
            # Check for common passwords
            common_passwords = ['password', '12345678', 'qwerty', 'abc123']
            if password1.lower() in common_passwords:
                raise ValidationError("This password is too common.")
        
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The two password fields didn't match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        if self.cleaned_data.get('phone_number'):
            user.phone_number = self.cleaned_data['phone_number']
        
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name', 'bio', 'profile_picture', 'phone_number')

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'phone_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes for better styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email
