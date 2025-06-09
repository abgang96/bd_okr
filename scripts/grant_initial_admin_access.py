import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okr.settings')
django.setup()

from teamsauth.models import TeamsProfile
from teamsauth.access_models import UserAccessMapping, AccessMaster

def main():
    """
    Script to grant admin master access to the first user in the database.
    This ensures there's at least one admin user who can manage the system.
    """
    print("Granting admin access to the initial user...")
    
    # Get the first active user
    try:
        user = TeamsProfile.objects.filter(isActive=True).first()
        
        if user:
            print(f"Found user: {user.user_name or user.teams_user_principal_name}")
            
            # Grant Add Objective access
            obj_access, created = UserAccessMapping.objects.get_or_create(
                user=user,
                access_id=AccessMaster.ADD_OBJECTIVE
            )
            if created:
                print(f"Added ADD_OBJECTIVE access for {user.user_name or user.teams_user_principal_name}")
            else:
                print(f"ADD_OBJECTIVE access already exists for {user.user_name or user.teams_user_principal_name}")
                
            # Grant Admin Master access
            admin_access, created = UserAccessMapping.objects.get_or_create(
                user=user,
                access_id=AccessMaster.ADMIN_MASTER
            )
            if created:
                print(f"Added ADMIN_MASTER access for {user.user_name or user.teams_user_principal_name}")
            else:
                print(f"ADMIN_MASTER access already exists for {user.user_name or user.teams_user_principal_name}")
                
            print("Initial admin access granted successfully!")
        else:
            print("No active users found in the database.")
            
    except Exception as e:
        print(f"Error granting initial admin access: {str(e)}")
        
if __name__ == "__main__":
    main()
