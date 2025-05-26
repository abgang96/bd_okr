from django.db import models
from teamsauth.models import TeamsProfile
from .weekly_discussions_models import FormData, QuestionMaster, OptionMapper, UserAnswerData

# Add authentication_type field to QuestionMaster
# You will need to create a migration to add this field
# Run: python manage.py makemigrations to create the migration

class ManagerReview(models.Model):
    """Stores manager reviews for weekly forms submitted by team members."""
    REVIEW_NOT_STARTED = 0
    REVIEW_IN_PROGRESS = 1
    REVIEW_COMPLETED = 2
    
    REVIEW_STATUS_CHOICES = [
        (REVIEW_NOT_STARTED, 'Not Started'),
        (REVIEW_IN_PROGRESS, 'In Progress'),
        (REVIEW_COMPLETED, 'Completed'),
    ]
    
    review_id = models.AutoField(primary_key=True)
    form = models.ForeignKey(FormData, on_delete=models.CASCADE, related_name='manager_reviews')
    manager = models.ForeignKey(TeamsProfile, on_delete=models.CASCADE, related_name='provided_reviews')
    status = models.IntegerField(choices=REVIEW_STATUS_CHOICES, default=REVIEW_NOT_STARTED)
    summary_comments = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('form', 'manager')
    
    def __str__(self):
        return f"Review by {self.manager.user_name} for {self.form.user.user_name}'s form ({self.form.entry_date})"

class ManagerAnswerData(models.Model):
    """Stores the answers provided by managers during their review."""
    answer_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(ManagerReview, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuestionMaster, on_delete=models.CASCADE)
    option = models.ForeignKey(OptionMapper, on_delete=models.CASCADE, null=True, blank=True)
    answer_description = models.TextField(null=True, blank=True, max_length=500)  # Larger limit for manager comments
    
    def __str__(self):
        if self.question.type == QuestionMaster.TYPE_DESCRIPTIVE:
            return f"Manager Review: {self.question.question_name}: {self.answer_description[:20]}..."
        else:
            return f"Manager Review: {self.question.question_name}: {self.option.option_desc if self.option else 'No option selected'}"
