from rest_framework import serializers
from .models import OKR, Task, Department, BusinessUnit, BusinessUnitOKRMapping, OkrUserMapping, TaskChallenges
from teamsauth.models import TeamsProfile
from teamsauth.serializers import TeamsProfileSerializer

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = ['business_unit_id', 'business_unit_name']

class BusinessUnitOKRMappingSerializer(serializers.ModelSerializer):
    business_unit = BusinessUnitSerializer(read_only=True)
    
    class Meta:
        model = BusinessUnitOKRMapping
        fields = ['business_unit']

class OkrUserMappingSerializer(serializers.ModelSerializer):
    user_details = TeamsProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = OkrUserMapping
        fields = ['id', 'user', 'okr', 'is_primary', 'created_at', 'user_details']
        extra_kwargs = {
            'user': {'write_only': True},
            'okr': {'write_only': True}
        }

class TaskChallengesSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TaskChallenges
        fields = ['id', 'task', 'challenge_name', 'status', 'status_display', 'due_date', 'remarks', 'created_at', 'updated_at']

class TaskSerializer(serializers.ModelSerializer):
    challenges = TaskChallengesSerializer(many=True, read_only=True)
    assigned_to_details = TeamsProfileSerializer(source='assigned_to', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Task
        fields = ['task_id', 'title', 'description', 'start_date', 'due_date', 
                 'status', 'status_display', 'assigned_to', 'assigned_to_details', 
                 'linked_to_okr', 'progress_percent', 'challenges']

class OKRSerializer(serializers.ModelSerializer):
    assigned_users_details = serializers.SerializerMethodField()
    business_units = BusinessUnitSerializer(many=True, read_only=True)
    business_unit_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )
    assigned_user_ids = serializers.ListField(
        child=serializers.CharField(),  # Using CharField for teams_id
        write_only=True,
        required=False
    )
    primary_user_id = serializers.CharField(required=False, write_only=True)  # Using CharField for teams_id
    department_details = DepartmentSerializer(source='department', read_only=True)
    child_okrs = serializers.SerializerMethodField()
    parent_okr_details = serializers.SerializerMethodField()
    
    class Meta:
        model = OKR
        fields = [
            'okr_id', 'name', 'description', 'assumptions', 'parent_okr', 
            'parent_okr_details', 'department', 'department_details', 
            'start_date', 'due_date', 'status', 'progress_percent', 
            'assigned_users_details', 'child_okrs', 'business_units', 
            'business_unit_ids', 'assigned_user_ids', 'primary_user_id', 
            'isMeasurable',
        ]
    
    def get_parent_okr_details(self, obj):
        if obj.parent_okr:
            return {
                'okr_id': obj.parent_okr.okr_id,
                'name': obj.parent_okr.name
            }
        return None
    
    def get_child_okrs(self, obj):
        # Get all child OKRs and return their basic details
        children = OKR.objects.filter(parent_okr=obj.okr_id)
        return [{
            'okr_id': child.okr_id,
            'name': child.name,
            'status': child.status,
            'progress_percent': child.progress_percent
        } for child in children]
    
    def get_assigned_users_details(self, obj):
        user_mappings = obj.user_mappings.all().select_related('user')
        return [
            {
                'user_id': mapping.user.teams_id,
                'name': mapping.user.user_name or mapping.user.teams_user_principal_name,
                'is_primary': mapping.is_primary
            }
            for mapping in user_mappings
        ]

    def create(self, validated_data):
        business_unit_ids = validated_data.pop('business_unit_ids', [])
        assigned_user_ids = validated_data.pop('assigned_user_ids', [])
        primary_user_id = validated_data.pop('primary_user_id', None)
        
        okr = OKR.objects.create(**validated_data)
        
        for business_unit_id in business_unit_ids:
            try:
                business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
                BusinessUnitOKRMapping.objects.create(okr=okr, business_unit=business_unit)
            except BusinessUnit.DoesNotExist:
                pass
        for teams_id in assigned_user_ids:
            is_primary = (teams_id == primary_user_id) if primary_user_id else (teams_id == assigned_user_ids[0])
            try:
                user = TeamsProfile.objects.get(teams_id=teams_id, isActive=True)
                OkrUserMapping.objects.create(
                    okr=okr,
                    user=user,
                    is_primary=is_primary
                )
            except TeamsProfile.DoesNotExist:
                pass
        
        return okr

    def update(self, instance, validated_data):
        business_unit_ids = validated_data.pop('business_unit_ids', None)
        assigned_user_ids = validated_data.pop('assigned_user_ids', None)
        primary_user_id = validated_data.pop('primary_user_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if business_unit_ids is not None:
            BusinessUnitOKRMapping.objects.filter(okr=instance).delete()
            for business_unit_id in business_unit_ids:
                try:
                    business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
                    BusinessUnitOKRMapping.objects.create(okr=instance, business_unit=business_unit)
                except BusinessUnit.DoesNotExist:
                    pass
        if assigned_user_ids is not None:
            OkrUserMapping.objects.filter(okr=instance).delete()
            for teams_id in assigned_user_ids:
                is_primary = (teams_id == primary_user_id) if primary_user_id else (teams_id == assigned_user_ids[0])
                try:
                    user = TeamsProfile.objects.get(teams_id=teams_id, isActive=True)
                    OkrUserMapping.objects.create(
                        okr=instance,
                        user=user,
                        is_primary=is_primary
                    )
                except TeamsProfile.DoesNotExist:
                    pass
        
        return instance