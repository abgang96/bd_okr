from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamsAuthView, MicrosoftAuthCallbackView, CurrentUserView, TeamsProfileViewSet, TeamMembersView
from .access_views import TeamsProfileWithAccessViewSet

router = DefaultRouter()
router.register(r'users', TeamsProfileViewSet)
router.register(r'user-access', TeamsProfileWithAccessViewSet, basename='user-access')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', TeamsAuthView.as_view(), name='teams-auth'),
    path('microsoft/callback', MicrosoftAuthCallbackView.as_view(), name='microsoft-callback'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('team-members/', TeamMembersView.as_view(), name='team-members'),
]