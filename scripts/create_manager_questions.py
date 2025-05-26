#!/usr/bin/env python
"""
Script to create manager questions for the weekly discussion functionality.
This script should be run after applying migrations for the manager review features.
"""

import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okr.settings')
django.setup()

from okrapi.weekly_discussions_models import QuestionMaster, OptionMapper

def create_manager_questions():
    """Create manager-specific questions for weekly review forms"""
    
    print("Creating manager questions...")
    
    # First, update all existing questions to be employee questions
    QuestionMaster.objects.all().update(authentication_type=QuestionMaster.AUTH_TYPE_EMPLOYEE)
    print(f"Updated {QuestionMaster.objects.count()} existing questions to employee type")
    
    # Create manager-specific questions
    manager_questions = [
        {
            "question_name": "What is your assessment of the team member's performance this week?",
            "type": QuestionMaster.TYPE_DESCRIPTIVE,
        },
        {
            "question_name": "What feedback and suggestions would you give to improve?",
            "type": QuestionMaster.TYPE_DESCRIPTIVE,
        },
        {
            "question_name": "How would you rate the team member's overall productivity this week?",
            "type": QuestionMaster.TYPE_MCQ,
        },
        {
            "question_name": "What achievements stood out in their weekly discussion?",
            "type": QuestionMaster.TYPE_DESCRIPTIVE,
        },
        {
            "question_name": "Are there any concerns you need to address with this team member?",
            "type": QuestionMaster.TYPE_DESCRIPTIVE,
        }
    ]
    
    # Create each manager question
    created_questions = []
    for q_data in manager_questions:
        question = QuestionMaster.objects.create(
            question_name=q_data["question_name"],
            type=q_data["type"],
            is_active=True,
            authentication_type=QuestionMaster.AUTH_TYPE_MANAGER
        )
        created_questions.append(question)
        print(f"Created manager question: {question.question_name}")
        
        # Add options for MCQ questions
        if question.type == QuestionMaster.TYPE_MCQ:
            options = [
                "Excellent - Exceeded expectations",
                "Good - Met all expectations",
                "Satisfactory - Met most expectations",
                "Needs improvement - Several expectations not met",
                "Unsatisfactory - Most expectations not met"
            ]
            
            for i, option_text in enumerate(options):
                option = OptionMapper.objects.create(
                    question=question,
                    option_desc=option_text,
                    option_value=i+1
                )
                print(f"  - Added option: {option.option_desc}")
    
    print(f"Successfully created {len(created_questions)} manager questions")
    
if __name__ == "__main__":
    create_manager_questions()
