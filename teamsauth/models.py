from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import jwt
from django.conf import settings
from datetime import datetime, timedelta
import requests


class TeamsProfile(models.Model):
    """
    Profile model for Microsoft Teams users.
    Extends the built-in Django User model with Teams-specific fields.
    """    # User fields
    teams_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    tenant_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    job_title = models.CharField(max_length=255, null=True, blank=True)
    manager_id = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    isActive = models.BooleanField(default=True)
    
    # Teams-specific profile data
    teams_user_principal_name = models.EmailField(null=True, blank=True)
    teams_profile_photo = models.URLField(max_length=1024, null=True, blank=True)
    
    # Authentication tokens
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Teams Profile - {self.user_name or self.teams_user_principal_name}"
    
    def update_tokens(self, access_token, refresh_token=None, expires_in=3600):
        """
        Update the stored tokens and their expiry time
        
        Args:
            access_token (str): The new access token
            refresh_token (str, optional): The new refresh token
            expires_in (int): Token expiry time in seconds (default 1 hour)
        """
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        self.save()
    
    def is_token_valid(self):
        """
        Check if the stored access token is still valid
        
        Returns:
            bool: True if the token exists and has not expired, False otherwise
        """
        if not self.access_token or not self.token_expiry:
            return False
        
        # Add 5 minutes buffer before expiry to ensure token is valid during use
        buffer_time = timedelta(minutes=5)
        return datetime.now() + buffer_time < self.token_expiry
    
    def validate_or_refresh_token(self):
        """
        Validate the current token and attempt to refresh it if expired
        
        Returns:
            str: Valid access token if available, None otherwise
        """
        if self.is_token_valid():
            return self.access_token
            
        if not self.refresh_token:
            return None
            
        try:
            # Example refresh token endpoint URL - should be configured in settings
            refresh_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': settings.MS_TEAMS_CLIENT_ID,
                'client_secret': settings.MS_TEAMS_CLIENT_SECRET,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(refresh_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.update_tokens(
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    expires_in=token_data.get('expires_in', 3600)
                )
                return self.access_token
                
        except Exception as e:
            # Log the error but don't raise it
            print(f"Error refreshing token: {str(e)}")
            
        return None