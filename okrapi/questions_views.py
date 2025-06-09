from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from okrapi.weekly_discussions_models import QuestionMaster, OptionMapper
from rest_framework import serializers

class QuestionMasterSerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionMaster
        fields = ['question_id', 'question_name', 'type', 'type_display', 'is_active', 'authentication_type']
    
    def get_type_display(self, obj):
        return obj.get_type_display()

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionMapper
        fields = ['option_id', 'option_desc']

class QuestionMasterDetailSerializer(QuestionMasterSerializer):
    options = OptionSerializer(many=True, read_only=True)
    
    class Meta(QuestionMasterSerializer.Meta):
        fields = QuestionMasterSerializer.Meta.fields + ['options']

class QuestionMasterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for question management
    """
    queryset = QuestionMaster.objects.all().order_by('question_id')
    serializer_class = QuestionMasterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['retrieve']:
            return QuestionMasterDetailSerializer
        return QuestionMasterSerializer
    
    def get_queryset(self):
        """Filter questions by authentication_type if specified"""
        queryset = QuestionMaster.objects.all().order_by('question_id')
        auth_type = self.request.query_params.get('auth_type')
        
        if auth_type is not None:
            try:
                auth_type_int = int(auth_type)
                queryset = queryset.filter(authentication_type=auth_type_int)
            except ValueError:
                pass
                
        return queryset
    
    @action(detail=True, methods=['post'])
    def add_option(self, request, pk=None):
        """Add option to a question"""
        try:
            question = self.get_object()
            if question.type != QuestionMaster.TYPE_MCQ:
                return Response(
                    {'error': 'Can only add options to multiple choice questions'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            option_desc = request.data.get('option_desc')
            if not option_desc:
                return Response(
                    {'error': 'Option description is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            option = OptionMapper.objects.create(
                question=question,
                option_desc=option_desc
            )
            
            serializer = OptionSerializer(option)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'])
    def remove_option(self, request, pk=None):
        """Remove an option from a question"""
        try:
            question = self.get_object()
            option_id = request.data.get('option_id')
            if not option_id:
                return Response(
                    {'error': 'Option ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            option = OptionMapper.objects.get(option_id=option_id, question=question)
            option.delete()
            
            return Response(
                {'message': 'Option deleted successfully'},
                status=status.HTTP_200_OK
            )
            
        except OptionMapper.DoesNotExist:
            return Response(
                {'error': 'Option not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
