from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('general', 'General User'),
        ('organizer', 'Organizer'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='general')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Add these to resolve reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_groups",  # Unique related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_permissions",  # Unique related_name
        related_query_name="customuser",
    )
    
    def is_organizer(self):
        return self.user_type == 'organizer'
    
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"