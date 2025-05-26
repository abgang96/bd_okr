"""
URL configuration for okr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from okrapi.views import OKRViewSet, TaskViewSet, DepartmentViewSet, BusinessUnitViewSet, OkrUserMappingViewSet, TaskChallengesViewSet
from okrapi.weekly_discussions_views import QuestionViewSet, WeeklyFormViewSet
from teamsauth.urls import router as teams_router

router = DefaultRouter()
router.register(r'okrs', OKRViewSet, basename='okr')
router.register(r'tasks', TaskViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'business-units', BusinessUnitViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'weekly-forms', WeeklyFormViewSet, basename='weekly-forms')
router.register(r'okr-user-mappings', OkrUserMappingViewSet)
router.register(r'task-challenges', TaskChallengesViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(teams_router.urls)),  # Include TeamsProfile API urls
    path('api/auth/', include('teamsauth.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
