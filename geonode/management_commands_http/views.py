#########################################################################
#
# Copyright (C) 2021 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import json

from rest_framework import permissions, serializers, status, views, viewsets, mixins
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.filters import ManagementCommandJobFilterSet
from geonode.management_commands_http.serializers import (
    ManagementCommandJobSerializer,
    ManagementCommandJobCreateSerializer,
)
from geonode.management_commands_http.utils.commands import (
    get_management_command_details,
    get_management_commands,
)
from geonode.management_commands_http.utils.jobs import start_task

from geonode.base.api.pagination import GeoNodeApiPagination


class ManagementCommandView(views.APIView):
    """
    Handle the exposed management commands usage:
      - GET: List of exposed commands
      - GET detail: Help for a specific command
      - POST: Create a job (and automatic runs) for a specific command.
    """

    permission_classes = [permissions.IsAdminUser]
    allowed_methods = ["GET", "POST"]

    def retrieve_details(self, cmd_name):
        # Object not found
        if cmd_name not in self.available_commands:
            return Response(
                {"success": False, "error": "Command not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Object Details: fetch help text of the Command
        cmd_details = get_management_command_details(cmd_name)
        return Response({"success": True, "error": None, "data": cmd_details})

    def list(self):
        return Response({
            "success": True,
            "error": None,
            "data": self.available_commands
        })

    def get(self, request, cmd_name=None):
        self.available_commands = get_management_commands()
        # List
        if cmd_name is None:
            return self.list()
        # Retrieve
        return self.retrieve_details(cmd_name)

    def post(self, request, cmd_name=None):
        """
        Creates and runs a management command job.
        Expects application/json content type in a following shape:
        {
            "args": [<arg1>, <arg2>],
            "kwargs: {<key1>: <val1>, <key2>: <val2>},
            "autostart": bool
        }
        By default, autostart is set to true.
        """
        create_serializer = ManagementCommandJobCreateSerializer(
            data={"command": cmd_name, "user": request.user, **request.data}
        )
        create_serializer.is_valid(raise_exception=True)
        args = create_serializer.validated_data.get('args', [])
        kwargs = create_serializer.validated_data.get('kwargs', {})
        autostart = create_serializer.validated_data.get('autostart', True)
        self.available_commands = get_management_commands()

        # Missing details
        if cmd_name is None:
            return Response(
                {"success": False, "error": "Method not allowed"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        # Object not found
        if cmd_name not in self.available_commands:
            return Response(
                {"success": False, "error": "Command not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Forbidden argument
        if "--help" in args:
            return Response(
                {
                    "success": False,
                    "error": 'Forbidden argument: "--help"',
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform Create
        obj_data = {
            "command": cmd_name,
            "user": request.user,
            "args": json.dumps(args),
            "kwargs": json.dumps(kwargs),
        }
        job = ManagementCommandJob.objects.create(**obj_data)

        # Start Job
        if autostart:
            start_task(job)

        serializer = ManagementCommandJobSerializer(instance=job)
        return Response(
            {
                "success": True,
                "error": None,
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )


class ManagementCommandJobViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAdminUser]
    queryset = ManagementCommandJob.objects.all().order_by("id")
    serializer_class = ManagementCommandJobSerializer
    filter_class = ManagementCommandJobFilterSet
    filter_backends = (DjangoFilterBackend,)
    pagination_class = GeoNodeApiPagination


    def initialize_request(self, request, *args, **kwargs):
        response = super(ManagementCommandJobViewSet, self).initialize_request(request, *args, **kwargs)
        print(f"self.action: {self.action}")
        return response


    def get_serializer_class(self):
        if self.action == "create":
            serializer = ManagementCommandJobCreateSerializer
        else:
            serializer = super().get_serializer_class()

        return serializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({"items": serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        autostart = serializer.validated_data.get('autostart', True)
        job = serializer.save()
        if autostart:
            start_task(job)
