from rest_framework import serializers
from .models import ManagementCommandJob


class ManagementCommandJobSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ManagementCommandJob
        fields = [
            'id',
            'command',
            'app_name',
            'user',
            'status',
            'created_at',
            'start_time',
            'end_time',
            'args',
            'kwargs',
            'celery_result_id',
            'output_message',
        ]
