from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import OKR, Task, Department, BusinessUnit, BusinessUnitOKRMapping, OkrUserMapping, TaskChallenges
from .serializers import (
    OKRSerializer, TaskSerializer, DepartmentSerializer,
    BusinessUnitSerializer, OkrUserMappingSerializer, TaskChallengesSerializer
)
from teamsauth.models import TeamsProfile
import logging

logger = logging.getLogger(__name__)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def list(self, request, *args, **kwargs):
        logger.info('Fetching all departments')
        response = super().list(request, *args, **kwargs)
        logger.info(f'Departments response: {response.data}')
        return response

class BusinessUnitViewSet(viewsets.ModelViewSet):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer
    permission_classes = []
    
    def get_queryset(self):
        queryset = BusinessUnit.objects.all()
        return queryset

class OKRViewSet(viewsets.ModelViewSet):
    queryset = OKR.objects.all().prefetch_related(
        'user_mappings', 'user_mappings__user',
        'business_unit_mappings', 'business_unit_mappings__business_unit',
        'child_okrs'
    ).select_related('department')
    serializer_class = OKRSerializer
    
    def get_queryset(self):
        # Get all OKRs since we need them for the tree
        queryset = super().get_queryset().select_related(
            'department', 'parent_okr'
        ).prefetch_related(
            'user_mappings__user',
            'business_unit_mappings__business_unit'
        )
        # Add debug logging
        logger.info(f'Fetching OKRs. Total count: {queryset.count()}')
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        data = request.data
        assigned_users = data.pop('assigned_users', None)
        business_units = data.pop('business_units', None)
        
        serializer = self.get_serializer(
            data=data, 
            context={
                'assigned_users': assigned_users,
                'business_units': business_units
            }
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        data = request.data.copy()
        assigned_users = data.pop('assigned_users', None)
        business_units = data.pop('business_units', None)
        
        serializer = self.get_serializer(
            instance, 
            data=data, 
            partial=partial, 
            context={
                'assigned_users': assigned_users,
                'business_units': business_units
            }
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)    
    def list(self, request, *args, **kwargs):
        logger.info('Fetching all OKRs')
        response = super().list(request, *args, **kwargs)
        logger.info(f'OKRs response: {response.data}')
        return response
    
    @action(detail=True, methods=['get'])
    def assigned_users(self, request, pk=None):
        """Get all users assigned to an OKR"""
        okr = self.get_object()
        user_mappings = okr.user_mappings.filter(user__isActive=True).select_related('user')
        
        assigned_users = [
            {
                'user_id': mapping.user.teams_id,
                'name': mapping.user.user_name or mapping.user.teams_user_principal_name,
                'is_primary': mapping.is_primary
            }
            for mapping in user_mappings
        ]
        
        return Response(assigned_users)

    @action(detail=True, methods=['post'])
    def assign_users(self, request, pk=None):
        """Assign multiple users to an OKR"""
        okr = self.get_object()
        users_data = request.data
        
        if not isinstance(users_data, list):
            return Response(
                {"error": "Expected a list of user assignments"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        okr.user_mappings.all().delete()
        created_mappings = []
        for idx, user_data in enumerate(users_data):
            teams_id = user_data.get('user_id')
            is_primary = user_data.get('is_primary', idx == 0)
            if not teams_id:
                continue
                
            try:
                user = TeamsProfile.objects.get(teams_id=teams_id, isActive=True)
                mapping = OkrUserMapping.objects.create(
                    okr=okr,
                    user=user,
                    is_primary=is_primary
                )
                created_mappings.append(mapping)
            except TeamsProfile.DoesNotExist:
                continue
        
        serializer = OkrUserMappingSerializer(created_mappings, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def business_units(self, request, pk=None):
        """Get all business units associated with an OKR."""
        okr = self.get_object()
        business_units = BusinessUnit.objects.filter(okr_mappings__okr=okr)
        serializer = BusinessUnitSerializer(business_units, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_business_units(self, request, pk=None):
        """Assign business units to an OKR."""
        okr = self.get_object()
        business_unit_ids = request.data
        
        if not isinstance(business_unit_ids, list):
            return Response(
                {"error": "Expected a list of business unit IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        BusinessUnitOKRMapping.objects.filter(okr=okr).delete()
        
        for business_unit_id in business_unit_ids:
            try:
                business_unit = BusinessUnit.objects.get(business_unit_id=business_unit_id)
                BusinessUnitOKRMapping.objects.create(okr=okr, business_unit=business_unit)
            except BusinessUnit.DoesNotExist:
                pass
                
        business_units = BusinessUnit.objects.filter(okr_mappings__okr=okr)
        serializer = BusinessUnitSerializer(business_units, many=True)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(assigned_to__isActive=True)
        linked_to_okr = self.request.query_params.get('linked_to_okr')
        
        if linked_to_okr:
            queryset = queryset.filter(linked_to_okr=linked_to_okr)
            
        return queryset

class OkrUserMappingViewSet(viewsets.ModelViewSet):
    queryset = OkrUserMapping.objects.all().select_related('user', 'okr')
    serializer_class = OkrUserMappingSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(user__isActive=True)
        okr_id = self.request.query_params.get('okr_id')
        teams_id = self.request.query_params.get('user_id')
        
        if okr_id:
            queryset = queryset.filter(okr_id=okr_id)
        if teams_id:
            queryset = queryset.filter(user__teams_id=teams_id)
            
        return queryset

class TaskChallengesViewSet(viewsets.ModelViewSet):
    queryset = TaskChallenges.objects.all()
    serializer_class = TaskChallengesSerializer
    def get_queryset(self):
        queryset = super().get_queryset().filter(task__assigned_to__isActive=True)
        task_id = self.request.query_params.get('task_id')
        status = self.request.query_params.get('status')
        
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if status is not None:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_task(self, request):
        """Get all challenges for a specific task"""
        task_id = request.query_params.get('task_id')
        if not task_id:            return Response(
                {"error": "task_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        challenges = TaskChallenges.objects.filter(task_id=task_id, task__assigned_to__isActive=True)
        serializer = self.get_serializer(challenges, many=True)
        return Response(serializer.data)
