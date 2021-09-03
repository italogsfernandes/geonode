from rest_framework import serializers
from .models import ManagementCommandJob


class ManagementCommandJobSerializer(serializers.HyperlinkedModelSerializer):
    """
    TODO: Think about separing create and read serializers
    """
    class Meta:
        model = ManagementCommandJob
        fields = ['id', 'command', 'app_name', 'status', 'args', 'kwargs']
