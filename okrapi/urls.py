from django.urls import path, include
from rest_framework import routers
from . import views
from .weekly_discussions_views import QuestionViewSet, WeeklyFormViewSet

router = routers.DefaultRouter()
router.register(r'okrs', views.OKRViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'business-units', views.BusinessUnitViewSet)
router.register(r'okr-user-mappings', views.OkrUserMappingViewSet)
router.register(r'task-challenges', views.TaskChallengesViewSet)

# Weekly discussions routes
router.register(r'questions', QuestionViewSet)
router.register(r'weekly-forms', WeeklyFormViewSet, basename='weekly-forms')

urlpatterns = [
    path('', include(router.urls)),
    
]