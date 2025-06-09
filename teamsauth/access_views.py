from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import TeamsProfile
from .access_models import UserAccessMapping, AccessMaster
from .access_serializers import TeamsProfileWithAccessSerializer, UserAccessMappingSerializer
from django.db import transaction

class TeamsProfileWithAccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint to manage user access rights
    """
    queryset = TeamsProfile.objects.filter(isActive=True)
    serializer_class = TeamsProfileWithAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def log_access_mappings(self):
        """Helper to log all access mappings"""
        print("\n=== All UserAccessMappings ===")
        all_mappings = UserAccessMapping.objects.all().select_related('user')
        print(f"Total access mappings found: {all_mappings.count()}")
        for mapping in all_mappings:
            print(f"Mapping: User={mapping.user.id}({mapping.user.teams_id}) - Access={mapping.access_id}")
        return all_mappings    
    
    @action(detail=False, methods=['get'])
    def check_current_user_access(self, request):
        """Returns the access rights for the current authenticated user"""
        user = request.user
        print("\n=== User Authentication Check ===")
        print(f"Current user details:")
        print(user)
        print(f"- Username: {user.username}")
        print(f"- Email: {user.email}")
        print(f"- ID: {user.id}")
        
        try:
            # Log all Teams profiles for debugging
            print("\n=== All TeamsProfiles ===")
            all_profiles = TeamsProfile.objects.all()
            print(f"Total TeamsProfiles found: {all_profiles.count()}")
            for profile in all_profiles:
                print(f"Profile: {profile.id} - Teams ID: {profile.teams_id} - Name: {profile.user_name or profile.teams_user_principal_name}")

            # Try to find the user's Teams profile with more flexible matching
            print(f"\n=== Looking for TeamsProfile with teams_id={user.username} ===")
            try:
                teams_profile = TeamsProfile.objects.get(teams_user_principal_name=user.email)
            except TeamsProfile.DoesNotExist:
                # Try alternative lookups if exact match fails
                teams_profile = TeamsProfile.objects.filter(
                    teams_user_principal_name__icontains=user.username
                ).first() or TeamsProfile.objects.filter(
                    user_name__icontains=user.username
                ).first()
                
                if not teams_profile:
                    print(f"No matching profile found for username: {user.username}")
                    raise TeamsProfile.DoesNotExist("No matching profile found")
            print(f"Found matching TeamsProfile: ID={teams_profile.id}, Name={teams_profile.user_name or teams_profile.teams_user_principal_name}")
            
            # Log all access mappings
            print("\n=== All UserAccessMappings ===")
            all_mappings = UserAccessMapping.objects.all()
            for mapping in all_mappings:
                print(f"Mapping: User={mapping.user.id} - Access={mapping.access_id}")
            
            # Check specific user's access
            print(f"\n=== Checking specific access for TeamsProfile ID={teams_profile.id} ===")            # Check all access mappings first
            self.log_access_mappings()
            
            # Check specific user's access
            print(f"\n=== Checking access for TeamsProfile ID={teams_profile.id} ===")
            add_objective_access = UserAccessMapping.objects.filter(
                user=teams_profile, access_id=AccessMaster.ADD_OBJECTIVE
            ).exists()
            admin_master_access = UserAccessMapping.objects.filter(
                user=teams_profile, access_id=AccessMaster.ADMIN_MASTER
            ).exists()
            
            print(f"ADD_OBJECTIVE constant value: {AccessMaster.ADD_OBJECTIVE}")
            print(f"ADMIN_MASTER constant value: {AccessMaster.ADMIN_MASTER}")
            print(f"Access rights results:")
            print(f"- add_objective_access: {add_objective_access}")
            print(f"- admin_master_access: {admin_master_access}")
            
            return Response({
                'add_objective_access': add_objective_access,
                'admin_master_access': admin_master_access
            })
        except TeamsProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_access(self, request, pk=None):
        """Update access rights for a user"""
        try:
            user = TeamsProfile.objects.get(teams_id=pk)
            add_objective = request.data.get('add_objective', False)
            admin_master = request.data.get('admin_master', False)
            
            with transaction.atomic():
                # Remove existing access rights
                UserAccessMapping.objects.filter(user=user).delete()
                
                # Add new access rights based on checkboxes
                if add_objective:
                    UserAccessMapping.objects.create(
                        user=user, 
                        access_id=AccessMaster.ADD_OBJECTIVE
                    )
                
                if admin_master:
                    UserAccessMapping.objects.create(
                        user=user, 
                        access_id=AccessMaster.ADMIN_MASTER
                    )
                
                return Response({
                    'message': 'Access rights updated successfully',
                    'add_objective': add_objective,
                    'admin_master': admin_master
                })
                
        except TeamsProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
