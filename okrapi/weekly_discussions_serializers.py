from rest_framework import serializers
import datetime
from .weekly_discussions_models import (
    QuestionMaster, OptionMapper, FormData, UserAnswerData,
    ManagerReview, ManagerAnswerData
)
from teamsauth.models import TeamsProfile

class OptionMapperSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionMapper
        fields = ['option_id', 'option_desc']

class QuestionMasterSerializer(serializers.ModelSerializer):
    options = OptionMapperSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionMaster
        fields = ['question_id', 'question_name', 'type', 'is_active', 'authentication_type', 'options']

class UserAnswerDataSerializer(serializers.ModelSerializer):
    option_desc = serializers.SerializerMethodField()
    question_text = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAnswerData
        fields = ['uad_id', 'question', 'question_text', 'option', 'option_desc', 'answer_description']
    
    def get_option_desc(self, obj):
        if obj.option:
            return obj.option.option_desc
        return None
        
    def get_question_text(self, obj):
        return obj.question.question_name

class ManagerAnswerDataSerializer(serializers.ModelSerializer):
    option_desc = serializers.SerializerMethodField()
    question_text = serializers.SerializerMethodField()
    
    class Meta:
        model = ManagerAnswerData
        fields = ['answer_id', 'question', 'question_text', 'option', 'option_desc', 'answer_description']
    
    def get_option_desc(self, obj):
        if obj.option:
            return obj.option.option_desc
        return None
        
    def get_question_text(self, obj):
        return obj.question.question_name

class ManagerReviewSerializer(serializers.ModelSerializer):
    answers = ManagerAnswerDataSerializer(many=True, read_only=True)
    status_display = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ManagerReview
        fields = ['review_id', 'form', 'manager', 'status', 'status_display',
                 'summary_comments', 'created_at', 'updated_at', 'answers', 'manager_name']
    
    def get_status_display(self, obj):
        return obj.get_status_display()
        
    def get_manager_name(self, obj):
        return obj.manager.user_name if hasattr(obj.manager, 'user_name') else obj.manager.teams_user_principal_name

class FormDataSerializer(serializers.ModelSerializer):
    answers = UserAnswerDataSerializer(many=True, read_only=True)
    manager_reviews = ManagerReviewSerializer(many=True, read_only=True)
    week = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    is_future = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    class Meta:
        model = FormData
        fields = ['form_id', 'user', 'entry_date', 'status', 'status_display', 'manager_review', 
                 'created_at', 'updated_at', 'answers', 'week', 'user_name', 'is_future', 'can_edit', 
                 'manager_reviews']
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    def get_week(self, obj):
        # Get the Monday date (entry_date is already the Monday of the week)
        monday_date = obj.entry_date
        # Calculate Friday date (4 days after Monday)
        friday_date = monday_date + datetime.timedelta(days=4)
        # Format dates as "dd MMM yyyy"
        monday_str = monday_date.strftime('%d %b %Y')
        friday_str = friday_date.strftime('%d %b %Y')
        # Return the date range
        return f"{monday_str} - {friday_str}"
    def get_user_name(self, obj):
        return obj.user.user_name if hasattr(obj.user, 'user_name') else obj.user.teams_user_principal_name
        
    def get_is_future(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        return obj.entry_date > today
    
    def get_can_edit(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        # Can edit if it's not a future form (can always edit past or current week forms)
        return obj.entry_date <= today

# Serializer for creating/updating form answers
class FormSubmitSerializer(serializers.Serializer):
    form_id = serializers.IntegerField()
    answers = serializers.ListField(child=serializers.DictField())
    
    def validate(self, data):
        form_id = data.get('form_id')
        
        try:
            form = FormData.objects.get(form_id=form_id)
        except FormData.DoesNotExist:
            raise serializers.ValidationError("Form does not exist")
        
        answers = data.get('answers', [])
        for answer in answers:
            question_id = answer.get('question_id')
            option_id = answer.get('option_id')
            answer_description = answer.get('answer_description')
            
            try:
                question = QuestionMaster.objects.get(question_id=question_id)
            except QuestionMaster.DoesNotExist:
                raise serializers.ValidationError(f"Question with ID {question_id} does not exist")
            
            if question.type == QuestionMaster.TYPE_DESCRIPTIVE:
                if answer_description and len(answer_description) > 250:
                    raise serializers.ValidationError(f"Answer for question {question_id} exceeds 250 characters")            
                elif question.type == QuestionMaster.TYPE_MCQ:
                    if option_id:
                        try:
                            option = OptionMapper.objects.get(option_id=option_id)
                            if option.question.question_id != question_id:
                                raise serializers.ValidationError(f"Option {option_id} does not belong to question {question_id}")
                        except OptionMapper.DoesNotExist:
                            raise serializers.ValidationError(f"Option with ID {option_id} does not exist")
        
        return data


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamsProfile
        fields = ['id', 'user_name', 'teams_user_principal_name', 'job_title', 'department', 'teams_id', 'manager_id']
        
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add debug logging
        print(f"\nDEBUG: Serializing team member:")
        print(f"  Instance data: {instance.__dict__}")
        print(f"  Serialized data: {ret}")
        return ret


# Serializer for submitting manager review
class ManagerReviewSubmitSerializer(serializers.Serializer):
    review_id = serializers.IntegerField(required=False)  # Optional for updates
    form_id = serializers.IntegerField()
    answers = serializers.ListField(child=serializers.DictField())
    summary_comments = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        form_id = data.get('form_id')
        
        try:
            form = FormData.objects.get(form_id=form_id)
        except FormData.DoesNotExist:
            raise serializers.ValidationError("Form does not exist")
        
        answers = data.get('answers', [])
        for answer in answers:
            question_id = answer.get('question_id')
            option_id = answer.get('option_id')
            answer_description = answer.get('answer_description')
            
            try:
                question = QuestionMaster.objects.get(question_id=question_id)
                # Check if this is a manager question
                if question.authentication_type not in [QuestionMaster.AUTH_TYPE_MANAGER, QuestionMaster.AUTH_TYPE_BOTH]:
                    raise serializers.ValidationError(f"Question {question_id} is not applicable for managers")
            except QuestionMaster.DoesNotExist:
                raise serializers.ValidationError(f"Question with ID {question_id} does not exist")
            
            if question.type == QuestionMaster.TYPE_DESCRIPTIVE:
                if answer_description and len(answer_description) > 500:
                    raise serializers.ValidationError(f"Answer for question {question_id} exceeds 500 characters")
            elif question.type == QuestionMaster.TYPE_MCQ:
                if option_id:
                    try:
                        option = OptionMapper.objects.get(option_id=option_id)
                        if option.question.question_id != question_id:
                            raise serializers.ValidationError(f"Option {option_id} does not belong to question {question_id}")
                    except OptionMapper.DoesNotExist:
                        raise serializers.ValidationError(f"Option with ID {option_id} does not exist")
        
        return data
