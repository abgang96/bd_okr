from django.db import models
from teamsauth.models import TeamsProfile

class QuestionMaster(models.Model):
    """Stores the master list of all questions that may appear in weekly forms."""
    TYPE_DESCRIPTIVE = 0
    TYPE_MCQ = 1
    
    TYPE_CHOICES = [
        (TYPE_DESCRIPTIVE, 'Descriptive'),
        (TYPE_MCQ, 'Multiple Choice'),
    ]
    
    AUTH_TYPE_EMPLOYEE = 0
    AUTH_TYPE_MANAGER = 1
    AUTH_TYPE_BOTH = 2
    
    AUTH_TYPE_CHOICES = [
        (AUTH_TYPE_EMPLOYEE, 'Employee'),
        (AUTH_TYPE_MANAGER, 'Manager'),
        (AUTH_TYPE_BOTH, 'Both'),
    ]
    
    question_id = models.AutoField(primary_key=True)
    question_name = models.TextField()
    type = models.IntegerField(choices=TYPE_CHOICES)
    is_active = models.BooleanField(default=True)  # To enable/disable questions
    authentication_type = models.IntegerField(choices=AUTH_TYPE_CHOICES, default=AUTH_TYPE_EMPLOYEE)
    
    def __str__(self):
        return self.question_name

class OptionMapper(models.Model):
    """Stores multiple choice options for each question where Type = 1."""
    option_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(QuestionMaster, on_delete=models.CASCADE, related_name='options')
    option_desc = models.TextField()
    
    def __str__(self):
        return f"{self.question.question_name} - {self.option_desc}"

class FormData(models.Model):
    """Tracks individual weekly form entries submitted or to be submitted by users."""
    STATUS_NOT_STARTED = 0
    STATUS_IN_PROGRESS = 1
    STATUS_SUBMITTED = 2
    
    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, 'Not Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SUBMITTED, 'Submitted'),
    ]
    
    form_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(TeamsProfile, on_delete=models.CASCADE, related_name='weekly_forms')
    entry_date = models.DateField()  # The Monday of the respective week
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_NOT_STARTED)
    manager_review = models.TextField(max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'entry_date')  # One form per user per week
    
    def __str__(self):
        return f"{self.user.user_name} - Week of {self.entry_date}"

class UserAnswerData(models.Model):
    """Stores the answers provided by a user for a given weekly form."""
    uad_id = models.AutoField(primary_key=True)
    form = models.ForeignKey(FormData, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuestionMaster, on_delete=models.CASCADE)
    option = models.ForeignKey(OptionMapper, on_delete=models.CASCADE, null=True, blank=True)
    answer_description = models.TextField(null=True, blank=True, max_length=250)  # For descriptive answers
    def __str__(self):
        if self.question.type == QuestionMaster.TYPE_DESCRIPTIVE:
            return f"{self.form.user.user_name} - {self.question.question_name}: {self.answer_description[:20]}..."
        else:
            return f"{self.form.user.user_name} - {self.question.question_name}: {self.option.option_desc if self.option else 'No option selected'}"


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
