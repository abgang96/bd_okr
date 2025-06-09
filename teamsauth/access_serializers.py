from rest_framework import serializers
from .models import TeamsProfile
from .access_models import UserAccessMapping, AccessMaster

class UserAccessMappingSerializer(serializers.ModelSerializer):
    access_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAccessMapping
        fields = ['id', 'user', 'access_id', 'access_name']
    
    def get_access_name(self, obj):
        return obj.get_access_id_display()

class TeamsProfileWithAccessSerializer(serializers.ModelSerializer):
    add_objective_access = serializers.SerializerMethodField()
    admin_master_access = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamsProfile
        fields = ['teams_id', 'user_name', 'teams_user_principal_name', 'isActive', 
                  'add_objective_access', 'admin_master_access']
    
    def get_add_objective_access(self, obj):
        return UserAccessMapping.objects.filter(
            user=obj,
            access_id=AccessMaster.ADD_OBJECTIVE
        ).exists()
    
    def get_admin_master_access(self, obj):
        return UserAccessMapping.objects.filter(
            user=obj,
            access_id=AccessMaster.ADMIN_MASTER
        ).exists()
