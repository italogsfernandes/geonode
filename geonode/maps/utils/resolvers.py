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
from geonode.maps.contants import _PERMISSION_MSG_GENERIC
from geonode.maps.models import Map
from geonode.utils import resolve_object


def resolve_map(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the Map by the provided typename and check the optional permission.
    """
    key = "urlsuffix" if Map.objects.filter(urlsuffix=id).exists() else "pk"

    map_obj = resolve_object(request, Map, {key: id}, permission=permission, permission_msg=msg, **kwargs)
    return map_obj
