from rest_framework import serializers
from .models import TeamsProfile

class TeamsProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamsProfile
        fields = ['id', 'teams_id', 'user_name', 'department', 'job_title', 'teams_user_principal_name', 'manager_id']