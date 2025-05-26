import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okr.settings')
django.setup()

from okrapi.weekly_discussions_models import QuestionMaster, OptionMapper

def create_sample_questions():
    # Clear existing data
    print("Clearing existing questions and options...")
    OptionMapper.objects.all().delete()
    QuestionMaster.objects.all().delete()
    
    # Create descriptive questions
    print("Creating descriptive questions...")
    q1 = QuestionMaster.objects.create(
        question_name="What challenges did you face this week?",
        type=QuestionMaster.TYPE_DESCRIPTIVE,
        is_active=True
    )
    
    q2 = QuestionMaster.objects.create(
        question_name="What achievements were you proud of this week?",
        type=QuestionMaster.TYPE_DESCRIPTIVE,
        is_active=True
    )
    
    q3 = QuestionMaster.objects.create(
        question_name="What are your priorities for next week?",
        type=QuestionMaster.TYPE_DESCRIPTIVE,
        is_active=True
    )
    
    # Create multiple choice questions
    print("Creating multiple choice questions...")
    q4 = QuestionMaster.objects.create(
        question_name="How would you rate your productivity this week?",
        type=QuestionMaster.TYPE_MCQ,
        is_active=True
    )
    
    # Add options for q4
    OptionMapper.objects.create(question=q4, option_desc="Very Low")
    OptionMapper.objects.create(question=q4, option_desc="Low")
    OptionMapper.objects.create(question=q4, option_desc="Average")
    OptionMapper.objects.create(question=q4, option_desc="High")
    OptionMapper.objects.create(question=q4, option_desc="Very High")
    
    q5 = QuestionMaster.objects.create(
        question_name="How do you feel about your work-life balance this week?",
        type=QuestionMaster.TYPE_MCQ,
        is_active=True
    )
    
    # Add options for q5
    OptionMapper.objects.create(question=q5, option_desc="Very Dissatisfied")
    OptionMapper.objects.create(question=q5, option_desc="Dissatisfied")
    OptionMapper.objects.create(question=q5, option_desc="Neutral")
    OptionMapper.objects.create(question=q5, option_desc="Satisfied")
    OptionMapper.objects.create(question=q5, option_desc="Very Satisfied")
    
    print("Sample questions created successfully!")

if __name__ == "__main__":
    print("Starting script to create sample questions...")
    create_sample_questions()
    print("Script finished!")
