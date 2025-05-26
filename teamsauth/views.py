import os
import json
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .serializers import TeamsProfileSerializer

from .models import TeamsProfile


class TeamsAuthView(APIView):
    """
    Authentication endpoint for Microsoft Teams SSO.
    Handles token validation and user authentication/creation.
    """
    permission_classes = [AllowAny]
    
    def generate_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        teams_token = request.data.get('token')
        print("[TeamsAuthView] Received token:", bool(teams_token))  # Log token presence
        
        if not teams_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if we're in DEBUG mode and using the development token shortcut
            if settings.DEBUG and teams_token.lower() == 'development':
                print("[TeamsAuthView] Using development mode")
                user, created = self.get_or_create_dev_user()
                tokens = self.generate_tokens(user)
                
                try:
                    profile = TeamsProfile.objects.get(teams_user_principal_name=user.email)
                except TeamsProfile.DoesNotExist:
                    profile = TeamsProfile.objects.create(
                        teams_id='dev-teams-id',
                        department='Development',
                        job_title='Developer',
                        teams_user_principal_name=user.email,
                        user_name='Dev User'
                    )
                
                # Store a dummy token for development
                profile.update_tokens(
                    access_token='dev-token',
                    refresh_token='dev-refresh-token',
                    expires_in=3600
                )
                print("[TeamsAuthView] Dev profile updated with tokens")
                
                return Response({
                    'tokens': tokens,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'department': profile.department,
                        'job_title': profile.job_title,
                        'teams_id': profile.teams_id,
                    }
                })
            
            # Normal token validation for production/real Teams tokens
            print("[TeamsAuthView] Validating Teams token")
            user_data = self.validate_teams_token(teams_token)
            if not user_data:
                return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get or create a user based on the Teams ID
            print("[TeamsAuthView] Getting or creating user")
            user, profile = self.get_or_create_user(user_data)
            
            # Store the Microsoft token in the profile
            print("[TeamsAuthView] Updating profile tokens")
            profile.update_tokens(
                access_token=teams_token,
                expires_in=3600  # Token typically expires in 1 hour
            )
            
            # Generate JWT tokens for our app
            tokens = self.generate_tokens(user)
            print("[TeamsAuthView] Generated JWT tokens")
            
            # Return user info and tokens
            return Response({
                'tokens': tokens,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'department': profile.department,
                    'job_title': profile.job_title,
                    'teams_id': profile.teams_id,
                }
            })
            
        except Exception as e:
            print("[TeamsAuthView] Error:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def get_or_create_dev_user(self):
        """Create or get a development user for testing"""
        try:
            user = User.objects.get(username='devuser')
            return user, False
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='devuser',
                email='dev@example.com',
                first_name='Development',
                last_name='User',
            )
            user.set_password('devpassword')
            user.is_active = True
            user.save()
            return user, True
    
    def validate_teams_token(self, token):
        """Validate Teams token with Microsoft Graph API and get user info"""
        graph_url = 'https://graph.microsoft.com/v1.0/me'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_or_create_user(self, user_data):
        """Get or create a user based on the Microsoft user data"""
        teams_id = user_data.get('id')
        email = user_data.get('mail') or user_data.get('userPrincipalName', '')
        username = email.split('@')[0] if '@' in email else email
        
        # First, try to find an existing user with the email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user if not found
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_data.get('givenName', ''),
                last_name=user_data.get('surname', '')
            )
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()

        # Try to find or create a teams profile with this teams_id
        try:
            profile = TeamsProfile.objects.get(teams_id=teams_id)
        except TeamsProfile.DoesNotExist:
            profile = TeamsProfile.objects.create(
                teams_id=teams_id,
                department=user_data.get('department', ''),
                job_title=user_data.get('jobTitle', ''),
                user_name=f"{user_data.get('givenName', '')} {user_data.get('surname', '')}".strip(),
                teams_user_principal_name=user_data.get('userPrincipalName', '')
            )

        # Update profile data
        profile.department = user_data.get('department', '')
        profile.job_title = user_data.get('jobTitle', '')
        profile.user_name = f"{user_data.get('givenName', '')} {user_data.get('surname', '')}".strip()
        profile.teams_user_principal_name = user_data.get('userPrincipalName', '')
        
        # Update manager ID if available
        if 'manager' in user_data:
            profile.manager_id = user_data['manager'].get('id')
            
        profile.save()
        
        return user, profile
        
    def generate_tokens(self, user):
        """Generate JWT tokens for the user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class MicrosoftAuthCallbackView(APIView):
    """
    Handle Microsoft OAuth code-to-token exchange and user creation/login
    """
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')
        email = request.data.get('email')
        name = request.data.get('name')
        
        if not access_token:
            return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get user info from the provided data
            user_data = {
                'mail': email,
                'displayName': name,
                'id': email  # Using email as Teams ID for simplicity
            }
            
            # Get or create a user based on the Teams ID
            user, profile = self.get_or_create_user(user_data)
            
            # Store the Microsoft token in the profile
            profile.update_tokens(
                access_token=access_token,
                expires_in=3600  # Token typically expires in 1 hour
            )
            
            # Generate JWT tokens for our app
            refresh = RefreshToken.for_user(user)
            tokens = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            
            # Return user info and tokens
            return Response({
                'tokens': tokens,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': profile.user_name,
                    'department': profile.department,
                    'job_title': profile.job_title,
                    'teams_id': profile.teams_id
                }
            })
            
        except Exception as e:
            print("[MicrosoftAuthCallbackView] Error:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_token_from_code(self, code, redirect_uri):
        """Exchange authorization code for an access token"""
        # Use your specific tenant ID instead of a placeholder
        tenant_id = settings.MS_GRAPH_TENANT_ID if settings.MS_GRAPH_TENANT_ID else '0f31460e-8f97-4bf6-9b20-fe837087ad59'
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        redir_uri="https://fe-okr-fi2.vercel.app/auth/microsoft-callback"
        
        token_data = {
            'client_id': settings.MS_GRAPH_CLIENT_ID,
            'client_secret': settings.MS_GRAPH_CLIENT_SECRET,
            'code': code,
            'redirect_uri': redir_uri,
            'grant_type': 'authorization_code',
            'scope': 'https://graph.microsoft.com/User.Read'
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            return response.json()
        
        print(f"Error exchanging code for token: {response.status_code} - {response.text}")
        return None
    
    def get_user_info(self, access_token):
        """Get user info from Microsoft Graph API"""
        graph_url = 'https://graph.microsoft.com/v1.0/me'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(user_data)
            user_id = user_data.get('id')
            
            # Fetch manager information as well
            manager_data = self.get_manager_info(user_id,access_token)
            if manager_data:
                user_data['manager'] = manager_data
                
            return user_data
        
        print(f"Error getting user info: {response.status_code} - {response.text}")
        return None
        
    def get_manager_info(self,user_id, access_token):
        """Get the user's manager information from Microsoft Graph API"""
        manager_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/manager'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(manager_url, headers=headers)
            print(user_id)
            print(response.json())
            if response.status_code == 200:
                manager_data = response.json()
                print(f"Manager data fetched successfully: {manager_data.get('displayName')} (ID: {manager_data.get('id')})")
                return manager_data
                
            # 404 can happen if the user doesn't have a manager, which is a valid case
            elif response.status_code == 404:
                print("User doesn't have a manager assigned")
                return None
                
            print(f"Error getting manager info: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            print(f"Exception when fetching manager: {str(e)}")
            return None
    
    def get_or_create_user(self, user_data):
        """Get or create a user based on the Microsoft user data"""
        teams_id = user_data.get('id')
        email = user_data.get('mail') or user_data.get('userPrincipalName', '')
        username = email.split('@')[0] if '@' in email else email
        
        # First, try to find an existing user with the email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user if not found
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_data.get('givenName', ''),
                last_name=user_data.get('surname', '')
            )
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()

        # Try to find or create a teams profile with this teams_id
        try:
            profile = TeamsProfile.objects.get(teams_id=teams_id)
        except TeamsProfile.DoesNotExist:
            profile = TeamsProfile.objects.create(
                teams_id=teams_id,
                department=user_data.get('department', ''),
                job_title=user_data.get('jobTitle', ''),
                teams_user_principal_name=user_data.get('userPrincipalName', '')
            )

        # Update profile data
        profile.department = user_data.get('department', '')
        profile.job_title = user_data.get('jobTitle', '')
        profile.teams_user_principal_name = user_data.get('userPrincipalName', '')
        
        # Update manager ID if available
        if 'manager' in user_data:
            profile.manager_id = user_data['manager'].get('id')
            
        profile.save()
        
        return user, profile
    
    def generate_tokens(self, user):
        """Generate JWT tokens for the user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CurrentUserView(APIView):
    """
    Get the current authenticated user information
    """
    def get(self, request):
        user = request.user
        try:
            # Look up profile by email instead of foreign key
            profile = TeamsProfile.objects.get(teams_user_principal_name=user.email)
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'department': profile.department,
                'job_title': profile.job_title,
                'teams_id': profile.teams_id,
            })
        except TeamsProfile.DoesNotExist:
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'department': None,
                'job_title': None,
                'teams_id': None,
            })


class TeamsProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing Teams users with search functionality
    """
    queryset = TeamsProfile.objects.all()
    serializer_class = TeamsProfileSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = TeamsProfile.objects.all()
        search_query = self.request.query_params.get('search', None)
        
        if search_query:
            queryset = queryset.filter(
                Q(user_name__icontains=search_query) |
                Q(teams_user_principal_name__icontains=search_query)
            )
        
        return queryset


class TeamMembersView(APIView):
    """
    View to list all team members for the current user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = TeamsProfile.objects.get(teams_user_principal_name=request.user.email)
            # Here you can add logic to determine if the user is a manager
            # For now, let's base it on their job title
            is_manager = 'manager' in profile.job_title.lower() if profile.job_title else False
            
            # Get the user's team members (this would be based on your business logic)
            # For example, users in the same department
            team_members = TeamsProfile.objects.filter(
                department=profile.department
            ).exclude(teams_user_principal_name=profile.teams_user_principal_name)
            
            return Response({
                'is_manager': is_manager,
                'teams': TeamsProfileSerializer(team_members, many=True).data
            })
        except TeamsProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)