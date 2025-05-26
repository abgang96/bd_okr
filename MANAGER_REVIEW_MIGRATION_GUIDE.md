# Migration Guide for Manager Review Functionality

This document outlines the steps required to implement the Manager Review functionality for Weekly Discussions.

## Database Changes

1. Apply the model changes to add `authentication_type` field to `QuestionMaster` model and create the new `ManagerReview` and `ManagerAnswerData` models:

```bash
python manage.py makemigrations
python manage.py migrate
```

2. Update existing questions to set the appropriate `authentication_type`:

```python
# Update existing questions to be employee questions
from okrapi.weekly_discussions_models import QuestionMaster

# Set all existing questions to be employee questions
QuestionMaster.objects.all().update(authentication_type=QuestionMaster.AUTH_TYPE_EMPLOYEE)
```

## Creating Manager Questions

Create manager-specific questions:

```python
from okrapi.weekly_discussions_models import QuestionMaster, OptionMapper

# Create manager questions
q1 = QuestionMaster.objects.create(
    question_name="What is your assessment of the team member's performance this week?",
    type=QuestionMaster.TYPE_DESCRIPTIVE,
    is_active=True,
    authentication_type=QuestionMaster.AUTH_TYPE_MANAGER
)

q2 = QuestionMaster.objects.create(
    question_name="What feedback and suggestions would you give to improve?",
    type=QuestionMaster.TYPE_DESCRIPTIVE,
    is_active=True,
    authentication_type=QuestionMaster.AUTH_TYPE_MANAGER
)

q3 = QuestionMaster.objects.create(
    question_name="How would you rate the team member's overall productivity this week?",
    type=QuestionMaster.TYPE_MCQ,
    is_active=True,
    authentication_type=QuestionMaster.AUTH_TYPE_MANAGER
)

# Add options for q3
OptionMapper.objects.create(question=q3, option_desc="Below Expectations")
OptionMapper.objects.create(question=q3, option_desc="Meeting Expectations")
OptionMapper.objects.create(question=q3, option_desc="Exceeding Expectations")
OptionMapper.objects.create(question=q3, option_desc="Outstanding")

q4 = QuestionMaster.objects.create(
    question_name="Did the team member meet all their commitments this week?",
    type=QuestionMaster.TYPE_MCQ,
    is_active=True,
    authentication_type=QuestionMaster.AUTH_TYPE_MANAGER
)

# Add options for q4
OptionMapper.objects.create(question=q4, option_desc="No, missed multiple commitments")
OptionMapper.objects.create(question=q4, option_desc="Partially met commitments")
OptionMapper.objects.create(question=q4, option_desc="Met most commitments")
OptionMapper.objects.create(question=q4, option_desc="Met all commitments")
```

## Replace API Views

Replace the existing weekly_discussions_views.py with the new version that includes manager-related API endpoints.

## Update Front-end Routes

Ensure the following Next.js routes are working:

- `/weekly-discussions` - User's own weekly discussions
- `/team-discussions` - List of team members and their discussions (for managers)
- `/team-discussions/review/[id]` - Review form for a manager to review a team member's submission

## Test the Workflow

1. Login as a manager user
2. Navigate to Weekly Discussions
3. Click on "My Team Discussions"
4. Find a team member with a submitted form
5. Click "Review Form"
6. Fill in the manager review
7. Submit the review
8. Verify that the review status is updated
