from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import TeamsProfile


class TeamsProfileInline(admin.StackedInline):
    model = TeamsProfile
    can_delete = False
    verbose_name_plural = 'Teams Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (TeamsProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_department', 'get_teams_id', 'is_staff')
    
    def get_department(self, obj):
        try:
            return obj.teams_profile.department
        except TeamsProfile.DoesNotExist:
            return None
    get_department.short_description = 'Department'
    
    def get_teams_id(self, obj):
        try:
            return obj.teams_profile.teams_id
        except TeamsProfile.DoesNotExist:
            return None
    get_teams_id.short_description = 'Teams ID'


# Re-register UserAdmin
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)