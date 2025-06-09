from django.db import models

class AccessMaster(models.IntegerChoices):
    """Enum for access types"""
    ADD_OBJECTIVE = 0, 'Add Objective'
    ADMIN_MASTER = 1, 'Admin Master'

class UserAccessMapping(models.Model):
    """Maps user permissions for specific access rights"""
    user = models.ForeignKey('teamsauth.TeamsProfile', on_delete=models.CASCADE, related_name='access_rights')
    access_id = models.IntegerField(choices=AccessMaster.choices)
    
    class Meta:
        unique_together = ('user', 'access_id')
        verbose_name = "User Access Right"
        verbose_name_plural = "User Access Rights"
    
    def __str__(self):
        return f"{self.user.user_name or self.user.teams_user_principal_name} - {self.get_access_id_display()}"
