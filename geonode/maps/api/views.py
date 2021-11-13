#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import logging
from uuid import uuid4

from drf_spectacular.utils import extend_schema
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.layers.api.serializers import DatasetSerializer
from geonode.maps.api.hook import hookset
from geonode.maps.models import Map
from geonode.maps.utils import decode_base64
from geonode.resource.manager import resource_manager

from .permissions import MapPermissionsFilter
from .serializers import MapLayerSerializer, MapSerializer

is_analytics_enabled = False
try:
    from geonode.base import register_event
    from geonode.monitoring.models import EventType

    is_analytics_enabled = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class MapViewSet(DynamicModelViewSet):
    """
    API endpoint that allows maps to be viewed or edited.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        MapPermissionsFilter,
    ]
    queryset = Map.objects.all().order_by("-date")
    serializer_class = MapSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(
        methods=["get"],
        responses={200: MapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def datasets(self, request, pk=None):
        map = self.get_object()
        resources = map.datasets
        return Response(MapLayerSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: DatasetSerializer(many=True)},
        description="API endpoint allowing to retrieve the local MapLayers.",
    )
    @action(detail=True, methods=["get"])
    def local_datasets(self, request, pk=None):
        map = self.get_object()
        resources = map.local_datasets
        return Response(DatasetSerializer(embed=True, many=True).to_representation(resources))

    def perform_create_using_hookset(self, serializer):
        if serializer.is_valid():
            hookset().perform_create(self, serializer)
            return serializer

    def perform_create(self, serializer):
        serializer.validated_data["owner"] = self.request.user
        serializer.validated_data["resource_type"] = "map"
        serializer.validated_data["uuid"] = str(uuid4())

        # Thumbnail
        thumbnail = serializer.validated_data.pop("thumbnail_url", "")

        # TODO: I'm reading the blob, it should not happen
        blob_map_data = serializer.validated_data["blob"]["map"]
        serializer.validated_data["center_x"] = blob_map_data["center"]["x"]
        serializer.validated_data["center_y"] = blob_map_data["center"]["y"]
        serializer.validated_data["projection"] = blob_map_data["projection"]
        serializer.validated_data["zoom"] = blob_map_data["zoom"]
        serializer.validated_data["srid"] = blob_map_data["projection"]

        # Create the objects and stores in `serializer.instance`
        super(MapViewSet, self).perform_create(serializer)
        instance = serializer.instance

        if is_analytics_enabled:
            register_event(self.request, EventType.EVENT_CREATE, instance)

        resource_manager.update(instance.uuid, instance=instance, notify=True)
        resource_manager.set_thumbnail(instance.uuid, instance=instance, overwrite=False)

        _map_thumbnail = thumbnail or instance.thumbnail_url
        _map_thumbnail_format = "png"

        try:
            (_map_thumbnail, _map_thumbnail_format) = decode_base64(_map_thumbnail)
        except Exception:
            if _map_thumbnail:
                _map_thumbnail_format = "link"

        if _map_thumbnail:
            if _map_thumbnail_format == "link":
                instance.thumbnail_url = _map_thumbnail
            else:
                _map_thumbnail_filename = f"map-{instance.uuid}-thumb.{_map_thumbnail_format}"
                instance.save_thumbnail(_map_thumbnail_filename, _map_thumbnail)

        return instance

    def perform_update(self, serializer):
        """Associate current user as task owner"""
        if serializer.is_valid():
            hookset().perform_update(self, serializer)
            return serializer


"""
from geonode.maps.signals import map_changed_signal

    dataset_names_before_changes = {lyr.alternate for lyr in instance.local_datasets}
    dataset_names_after_changes = {lyr.alternate for lyr in instance.local_datasets}
    if dataset_names_before_changes != dataset_names_after_changes:
        map_changed_signal.send_robust(sender=instance, what_changed="datasets")


    def save(self, *args, **kwargs):
        # TODO: put it in a better place, and delete some fields of "Map"
        # TODO: just for the moment and then remove the zoom column
        request = self.context["request"]

        # Get map_obj
        map_id = self.validated_data.get("id", None)
        map_obj = None
        if map_id:
            map_obj = resolve_map(
                request,
                str(map_id),
                'base.change_resourcebase',
                _PERMISSION_MSG_SAVE
            )
"""

"""
In normal condictions:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

"""
