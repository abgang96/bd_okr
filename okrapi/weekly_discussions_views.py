from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .weekly_discussions_models import (
    QuestionMaster, OptionMapper, FormData, UserAnswerData,
    ManagerReview, ManagerAnswerData
)
from teamsauth.models import TeamsProfile
from .weekly_discussions_serializers import (
    QuestionMasterSerializer, OptionMapperSerializer, 
    FormDataSerializer, UserAnswerDataSerializer, 
    FormSubmitSerializer, TeamMemberSerializer,
    ManagerReviewSerializer, ManagerReviewSubmitSerializer,
    ManagerAnswerDataSerializer
)

def get_monday_of_week(date):
    """Get the Monday of the week for a given date."""
    return date - timedelta(days=date.weekday())

def get_teams_profile(user):
    """Get or create a TeamsProfile for a Django User object"""
    if not user or user.is_anonymous:
        return None
        
    # Try to find by email
    if user.email:
        profile = TeamsProfile.objects.filter(teams_user_principal_name=user.email).first()
        if profile:
            return profile
    
    # In debug mode, create a profile for testing
    if settings.DEBUG:
        profile, created = TeamsProfile.objects.get_or_create(
            user_name=user.username,
            teams_user_principal_name=user.email or f"{user.username}@example.com"
        )
        return profile
    
    return None

def generate_forms_for_user(user):
    """Generate 8 weeks of forms for a user (4 past, 4 future)"""
    today = timezone.now().date()
    current_monday = get_monday_of_week(today)
    
    # Generate 4 past weeks (including current) and 4 future weeks
    weeks = []
    for i in range(-3, 5):
        week_monday = current_monday + timedelta(weeks=i)
        weeks.append(week_monday)
    
    # Create FormData entries for any missing weeks
    created_forms = []
    for week_date in weeks:
        form, created = FormData.objects.get_or_create(
            user=user,
            entry_date=week_date,
            defaults={
                'status': FormData.STATUS_NOT_STARTED
            }
        )
        if created:
            created_forms.append(form)
    
    return created_forms

def get_team_members(manager_profile):
    """Get all team members under a manager"""
    print("\n=== DEBUG: get_team_members function ===")
    print(f"Manager Profile Object: {manager_profile}")
    print(f"Manager Profile Dict: {manager_profile.__dict__ if manager_profile else None}")
    
    if not manager_profile:
        print("DEBUG: No manager profile provided")
        return TeamsProfile.objects.none()
    
    print(f"\nDEBUG: Looking for team members with manager_id={manager_profile.teams_id}")
    print(f"DEBUG: Manager teams_id type: {type(manager_profile.teams_id)}")
    
    team_members = TeamsProfile.objects.filter(manager_id=manager_profile.teams_id)
    
    print("\nDEBUG: Team Members Query:")
    print(f"SQL Query: {str(team_members.query)}")
    print(f"Found {team_members.count()} team members")
    
    # Print each team member's details
    for member in team_members:
        print(f"\nTeam Member Details:")
        print(f"  Name: {member.user_name}")
        print(f"  Teams ID: {member.teams_id}")
        print(f"  Email: {member.teams_user_principal_name}")
        print(f"  Manager ID: {member.manager_id}")
    
    return team_members

def create_manager_reviews(manager, team_member_forms):
    """Create manager review objects for forms that don't have them"""
    created_reviews = []
    
    for form in team_member_forms:
        # Only create for submitted forms without a manager review
        if form.status == FormData.STATUS_SUBMITTED:
            review, created = ManagerReview.objects.get_or_create(
                form=form,
                manager=manager,
                defaults={
                    'status': ManagerReview.REVIEW_NOT_STARTED
                }
            )
            if created:
                created_reviews.append(review)
                
    return created_reviews

def generate_forms_for_user(user):
    """Generate 8 weeks of forms for a user (4 past, 4 future)"""
    today = timezone.now().date()
    current_monday = get_monday_of_week(today)
    
    # Generate 4 past weeks (including current) and 4 future weeks
    weeks = []
    for i in range(-3, 5):
        week_monday = current_monday + timedelta(weeks=i)
        weeks.append(week_monday)
    
    # Create FormData entries for any missing weeks
    created_forms = []
    for week_date in weeks:
        form, created = FormData.objects.get_or_create(
            user=user,
            entry_date=week_date,
            defaults={
                'status': FormData.STATUS_NOT_STARTED
            }
        )
        if created:
            created_forms.append(form)
    
    return created_forms

class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for retrieving questions"""
    queryset = QuestionMaster.objects.filter(is_active=True)
    serializer_class = QuestionMasterSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def employee_questions(self, request):
        """Get questions for employees"""
        questions = QuestionMaster.objects.filter(
            is_active=True,
            authentication_type__in=[QuestionMaster.AUTH_TYPE_EMPLOYEE, QuestionMaster.AUTH_TYPE_BOTH]
        )
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def manager_questions(self, request):
        """Get questions for managers"""
        questions = QuestionMaster.objects.filter(
            is_active=True,
            authentication_type__in=[QuestionMaster.AUTH_TYPE_MANAGER, QuestionMaster.AUTH_TYPE_BOTH]
        )
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)

class WeeklyFormViewSet(viewsets.ModelViewSet):
    """API endpoint for managing weekly discussion forms"""
    serializer_class = FormDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get TeamsProfile for the current user
        try:
            user_profile = get_teams_profile(self.request.user)
            if not user_profile:
                return FormData.objects.none()
            
            # Generate forms if they don't exist
            generate_forms_for_user(user_profile)
            
            # Return forms for the user
            return FormData.objects.filter(user=user_profile).order_by('-entry_date')
        except Exception as e:
            print(f"Error in get_queryset: {str(e)}")            
            return FormData.objects.none()  # Return empty queryset on error
    
    @action(detail=False, methods=['get'])
    def my_forms(self, request):
        """Get the weekly forms for the current user"""
        forms = self.get_queryset()
        serializer = self.get_serializer(forms, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'])
    def my_team_members(self, request):
        """Get all team members under the current user as manager"""
        print("\n=== DEBUG: my_team_members endpoint ===")
        print(f"Request user: {request.user}")
        print(f"Request user email: {request.user.email}")
        
        user_profile = get_teams_profile(request.user)
        print(f"\nDEBUG: Retrieved user profile:")
        print(f"- Profile object: {user_profile}")
        if user_profile:
            print(f"- User name: {user_profile.user_name}")
            print(f"- Teams ID: {user_profile.teams_id}")
            print(f"- Email: {user_profile.teams_user_principal_name}")
            print(f"- Manager ID: {user_profile.manager_id}")
        
        if not user_profile:
            print("DEBUG: User profile not found")
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        team_members = get_team_members(user_profile)
        
        # Print the serialized data for debugging
        serializer = TeamMemberSerializer(team_members, many=True)
        print("\nDEBUG: Serialized response data:")
        print(serializer.data)
        
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def team_member_forms(self, request):
        """Get forms for team members under the current user as manager"""
        user_profile = get_teams_profile(request.user)
        if not user_profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # Get all team members
        team_members = get_team_members(user_profile)
        if not team_members.exists():
            return Response([])
            
        # Get forms for all team members
        team_member_forms = FormData.objects.filter(user__in=team_members).order_by('user__user_name', '-entry_date')
        
        # Create manager review objects for submitted forms
        create_manager_reviews(user_profile, team_member_forms.filter(status=FormData.STATUS_SUBMITTED))
        
        serializer = self.get_serializer(team_member_forms, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get questions and existing answers for a specific form"""
        try:
            # Find the user profile
            user_profile = get_teams_profile(request.user)
            if not user_profile:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            form = FormData.objects.get(pk=pk, user=user_profile)
            
            # Check if the form is for a future week
            today = timezone.now().date()
            if form.entry_date > today:
                return Response(
                    {"error": "Cannot fill forms for future weeks"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except FormData.DoesNotExist:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)
          # Get all active employee questions
        questions = QuestionMaster.objects.filter(
            is_active=True,
            authentication_type__in=[QuestionMaster.AUTH_TYPE_EMPLOYEE, QuestionMaster.AUTH_TYPE_BOTH]
        )
        question_serializer = QuestionMasterSerializer(questions, many=True)
        
        # Get existing answers for this form
        answers = UserAnswerData.objects.filter(form=form)
        answer_serializer = UserAnswerDataSerializer(answers, many=True)
        return Response({
            "form": FormDataSerializer(form).data,
            "questions": question_serializer.data,
            "answers": answer_serializer.data
        })
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit answers for a form"""
        try:
            # Find the user profile
            user_profile = get_teams_profile(request.user)
            print("\n=== DEBUG: Form Submit ===")
            print(f"Submitting form {pk} for user {user_profile}")
            
            if not user_profile:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            form = FormData.objects.get(pk=pk, user=user_profile)
            print(f"Initial form status: {form.status} ({form.get_status_display()})")
            
            # Check if the form is for a future week
            today = timezone.now().date()
            if form.entry_date > today:
                return Response(
                    {"error": "Cannot submit forms for future weeks"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except FormData.DoesNotExist:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate the submitted data
        serializer = FormSubmitSerializer(data={
            'form_id': pk,
            'answers': request.data.get('answers', [])
        })
        
        if not serializer.is_valid():
            print("Form validation failed:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the answers
        with transaction.atomic():
            print("Processing answers...")
            # Clear existing answers for this form
            UserAnswerData.objects.filter(form=form).delete()
            
            # Save new answers
            answers_data = serializer.validated_data['answers']
            for answer_data in answers_data:
                question_id = answer_data.get('question_id')
                option_id = answer_data.get('option_id')
                answer_description = answer_data.get('answer_description')
                
                question = QuestionMaster.objects.get(question_id=question_id)
                
                # Create the answer record
                answer = UserAnswerData(
                    form=form,
                    question=question
                )
                
                if question.type == QuestionMaster.TYPE_DESCRIPTIVE:
                    answer.answer_description = answer_description
                elif question.type == QuestionMaster.TYPE_MCQ and option_id:
                    answer.option_id = option_id
                
                answer.save()
            
            # Update form status to submitted
            form.status = FormData.STATUS_SUBMITTED
            form.save()
            print(f"Updated form status to: {form.status} ({form.get_status_display()})")
            
            # Create manager review record if manager exists
            if hasattr(user_profile, 'manager_id') and user_profile.manager_id:
                print(f"Creating manager review for manager_id: {user_profile.manager_id}")
                # Try to find the manager's profile
                manager_profile = TeamsProfile.objects.filter(teams_id=user_profile.manager_id).first()
                if manager_profile:
                    review, created = ManagerReview.objects.get_or_create(
                        form=form,
                        manager=manager_profile,
                        defaults={
                            'status': ManagerReview.REVIEW_NOT_STARTED
                        }
                    )
                    print(f"Manager review {'created' if created else 'found'} with status: {review.status} ({review.get_status_display()})")
                else:
                    print("Manager profile not found")
        
        # Double check the final form status
        form.refresh_from_db()
        print(f"Final form status check: {form.status} ({form.get_status_display()})")
        return Response({"message": "Form submitted successfully"}, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'])
    def update_submission(self, request, pk=None):
        """Update answers for an already submitted form"""
        try:
            # Find the user profile
            user_profile = get_teams_profile(request.user)
            if not user_profile:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            form = FormData.objects.get(pk=pk, user=user_profile)
            
            # Validate the submitted data
            serializer = FormSubmitSerializer(data={
                'form_id': pk,
                'answers': request.data.get('answers', [])
            })
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Process the answers
            with transaction.atomic():
                # Clear existing answers for this form
                UserAnswerData.objects.filter(form=form).delete()
                
                # Save new answers
                answers_data = serializer.validated_data['answers']
                for answer_data in answers_data:
                    question_id = answer_data.get('question_id')
                    option_id = answer_data.get('option_id')
                    answer_description = answer_data.get('answer_description')
                    
                    question = QuestionMaster.objects.get(question_id=question_id)
                    
                    # Create the answer record
                    answer = UserAnswerData(
                        form=form,
                        question=question
                    )
                    
                    if question.type == QuestionMaster.TYPE_DESCRIPTIVE:
                        answer.answer_description = answer_description
                    elif question.type == QuestionMaster.TYPE_MCQ and option_id:
                        answer.option_id = option_id
                    
                    answer.save()
                  # Re-save with submitted status in case it was changed
                form.status = FormData.STATUS_SUBMITTED
                form.save()
                
                # Reset manager reviews to not started
                ManagerReview.objects.filter(form=form).update(status=ManagerReview.REVIEW_NOT_STARTED)
            
            return Response({"message": "Form updated successfully"}, status=status.HTTP_200_OK)
        except FormData.DoesNotExist:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)
    @action(detail=True, methods=['get'])
    def manager_review_details(self, request, pk=None):
        """Get manager review details for a specific form"""
        try:
            form = FormData.objects.get(pk=pk)
            
            # Check if current user is the manager for this form
            user_profile = get_teams_profile(request.user)
            print("\n=== DEBUG: Manager Review Details ===")
            print(f"Form ID: {pk}")
            print(f"Form User: {form.user}")
            print(f"Manager Profile: {user_profile}")
            
            if not user_profile:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            # Find the manager review for this form by this manager
            try:
                manager_review = ManagerReview.objects.get(form=form, manager=user_profile)
                print(f"Found existing manager review, status: {manager_review.get_status_display()}")
            except ManagerReview.DoesNotExist:
                # Create a new manager review if it doesn't exist
                if form.user.manager_id == user_profile.teams_id:
                    manager_review = ManagerReview.objects.create(
                        form=form,
                        manager=user_profile,
                        status=ManagerReview.REVIEW_NOT_STARTED
                    )
                    print("Created new manager review")
                else:
                    print("User is not authorized to review this form")
                    return Response(
                        {"error": "You are not authorized to review this form"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get all manager questions
            questions = QuestionMaster.objects.filter(
                is_active=True,
                authentication_type__in=[QuestionMaster.AUTH_TYPE_MANAGER, QuestionMaster.AUTH_TYPE_BOTH]
            )
            question_serializer = QuestionMasterSerializer(questions, many=True)
            
            # Get existing manager answers for this review
            manager_answers = ManagerAnswerData.objects.filter(review=manager_review)
            answer_serializer = ManagerAnswerDataSerializer(manager_answers, many=True)
            
            # Get employee answers for reference
            employee_answers = UserAnswerData.objects.filter(form=form)
            employee_answer_serializer = UserAnswerDataSerializer(employee_answers, many=True)
            
            # Add can_edit flag to response
            response_data = {
                "form": FormDataSerializer(form).data,
                "review": ManagerReviewSerializer(manager_review).data,
                "manager_questions": question_serializer.data,
                "manager_answers": answer_serializer.data,
                "employee_answers": employee_answer_serializer.data,
                "can_edit": True  # Always allow editing of manager reviews
            }
            
            print("Response data prepared:")
            print(f"- Questions count: {len(questions)}")
            print(f"- Manager answers count: {len(manager_answers)}")
            print(f"- Employee answers count: {len(employee_answers)}")
            
            return Response(response_data)
            
        except FormData.DoesNotExist:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def submit_manager_review(self, request, pk=None):
        """Submit manager review for a form"""
        try:
            form = FormData.objects.get(pk=pk)
            
            # Check if current user is the manager for this form
            user_profile = get_teams_profile(request.user)
            if not user_profile:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
            # Find or create the manager review
            try:
                manager_review = ManagerReview.objects.get(form=form, manager=user_profile)
            except ManagerReview.DoesNotExist:
                if form.user.manager_id == user_profile.teams_id:
                    manager_review = ManagerReview.objects.create(
                        form=form,
                        manager=user_profile,
                        status=ManagerReview.REVIEW_NOT_STARTED
                    )
                else:
                    return Response(
                        {"error": "You are not authorized to review this form"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Validate the submitted data
            serializer = ManagerReviewSubmitSerializer(data={
                'form_id': pk,
                'review_id': manager_review.review_id,
                'answers': request.data.get('answers', []),
                'summary_comments': request.data.get('summary_comments', '')
            })
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Process the answers
            with transaction.atomic():
                # Clear existing manager answers for this review
                ManagerAnswerData.objects.filter(review=manager_review).delete()
                
                # Save new answers
                answers_data = serializer.validated_data['answers']
                for answer_data in answers_data:
                    question_id = answer_data.get('question_id')
                    option_id = answer_data.get('option_id')
                    answer_description = answer_data.get('answer_description')
                    
                    question = QuestionMaster.objects.get(question_id=question_id)
                    
                    # Create the answer record
                    answer = ManagerAnswerData(
                        review=manager_review,
                        question=question
                    )
                    
                    if question.type == QuestionMaster.TYPE_DESCRIPTIVE:
                        answer.answer_description = answer_description
                    elif question.type == QuestionMaster.TYPE_MCQ and option_id:
                        answer.option_id = option_id
                    
                    answer.save()
                
                # Update manager review status
                manager_review.status = ManagerReview.REVIEW_COMPLETED
                manager_review.summary_comments = serializer.validated_data.get('summary_comments', '')
                manager_review.save()
                
                # Update form's manager_review field for backward compatibility
                form.manager_review = serializer.validated_data.get('summary_comments', '')
                form.save()
            
            return Response({"message": "Manager review submitted successfully"}, status=status.HTTP_200_OK)
            
        except FormData.DoesNotExist:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def team_metrics(self, request):
        """Get metrics for the team's weekly discussions"""
        user_profile = get_teams_profile(request.user)
        if not user_profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # Get all team members
        team_members = get_team_members(user_profile)
        if not team_members.exists():
            return Response({
                "total_forms": 0,
                "completed_forms": 0,
                "completion_rate": 0,
                "completed_reviews": 0,
                "pending_reviews": 0
            })
        
        # Get stats for current and past weeks (exclude future)
        today = timezone.now().date()
        
        # Get all non-future forms for team members
        team_forms = FormData.objects.filter(
            user__in=team_members,
            entry_date__lte=today
        )
        
        # Calculate metrics
        total_forms = team_forms.count()
        completed_forms = team_forms.filter(status=FormData.STATUS_SUBMITTED).count()
        completion_rate = (completed_forms / total_forms * 100) if total_forms > 0 else 0
        
        # Reviews stats
        reviews = ManagerReview.objects.filter(
            form__in=team_forms.filter(status=FormData.STATUS_SUBMITTED),
            manager=user_profile
        )
        
        completed_reviews = reviews.filter(status=ManagerReview.REVIEW_COMPLETED).count()
        pending_reviews = reviews.filter(
            status__in=[ManagerReview.REVIEW_NOT_STARTED, ManagerReview.REVIEW_IN_PROGRESS]
        ).count()
        
        return Response({
            "total_forms": total_forms,
            "completed_forms": completed_forms,
            "completion_rate": round(completion_rate, 1),
            "completed_reviews": completed_reviews,
            "pending_reviews": pending_reviews
        })
