from django.urls import path, include
from rest_framework import routers
from . import views
from .weekly_discussions_views import QuestionViewSet, WeeklyFormViewSet
from .questions_views import QuestionMasterViewSet

router = routers.DefaultRouter()

# Weekly discussions routes
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'weekly-forms', WeeklyFormViewSet, basename='weekly-forms')

# Admin master routes
router.register(r'questions-master', QuestionMasterViewSet, basename='questions-master')

urlpatterns = [
    path('', include(router.urls)),
]