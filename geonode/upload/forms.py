#########################################################################
#
# Copyright (C) 2018 OSGeo
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
import smart_open  # TODO: remove if not needed

from django import forms
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from geonode.upload.models import UploadSizeLimit

from .. import geoserver
from ..utils import check_ogc_backend
from ..layers.forms import JSONField

from .upload_validators import validate_uploaded_files


logger = logging.getLogger(__name__)


class LayerUploadForm(forms.Form):
    base_file = forms.FileField(required=False)
    base_file_path = forms.CharField(required=False) # Todo: create smartopen URI field
    dbf_file = forms.FileField(required=False)
    dbf_file_path = forms.CharField(required=False) # Todo: create smartopen URI field
    shx_file = forms.FileField(required=False)
    shx_file_path = forms.CharField(required=False) # Todo: create smartopen URI field
    prj_file = forms.FileField(required=False)
    prj_file_path = forms.CharField(required=False) # Todo: create smartopen URI field
    xml_file = forms.FileField(required=False)
    xml_file_path = forms.CharField(required=False) # Todo: create smartopen URI field
    charset = forms.CharField(required=False)

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        sld_file = forms.FileField(required=False)
        sld_file_path = forms.CharField(required=False) # Todo: create smartopen URI field

    time = forms.BooleanField(required=False)

    mosaic = forms.BooleanField(required=False)
    append_to_mosaic_opts = forms.BooleanField(required=False)
    append_to_mosaic_name = forms.CharField(required=False)
    mosaic_time_regex = forms.CharField(required=False)
    mosaic_time_value = forms.CharField(required=False)
    time_presentation = forms.CharField(required=False)
    time_presentation_res = forms.IntegerField(required=False)
    time_presentation_default_value = forms.CharField(required=False)
    time_presentation_reference_value = forms.CharField(required=False)

    abstract = forms.CharField(required=False)
    dataset_title = forms.CharField(required=False)
    permissions = JSONField()

    metadata_uploaded_preserve = forms.BooleanField(required=False)
    metadata_upload_form = forms.BooleanField(required=False)
    style_upload_form = forms.BooleanField(required=False)

    spatial_files = [
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "xml_file",
    ]
    # Adding style file based on the backend
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        spatial_files.append('sld_file')

    spatial_files = tuple(spatial_files)

    def clean(self):
        cleaned = super().clean()
        base_file = self.cleaned_data.get('base_file')
        base_file_path = self.cleaned_data.get('base_file_path')

        if not base_file and not base_file_path and "base_file" not in self.errors and "base_file_path" not in self.errors:
            logger.error("Base file must be a file or url.")
            raise forms.ValidationError(_("Base file must be a file or url."))

        if base_file and base_file_path:
            logger.error("Base file cannot have both a file and a url.")
            raise forms.ValidationError(
                _("Base file cannot have both a file and a url."))

        if self.errors:
            # Something already went wrong
            return cleaned

        self.validate_smart_open_files(cleaned)

        self.validate_files_sum_of_sizes()
        uploaded_files = self._get_uploaded_files()
        uploaded_files_paths = self._get_files_paths()
        # Todo: get file name not based on url, it sometimes can be misleading
        base_file = cleaned.get("base_file", None)
        base_file_name = base_file.name if base_file else cleaned.get("base_file_path").uri_path

        valid_extensions = validate_uploaded_files(
            cleaned=cleaned,
            uploaded_files=uploaded_files,
            uploaded_files_paths=uploaded_files_paths,
            field_spatial_types=self.spatial_files,
            base_file_name=base_file_name,
        )
        cleaned["valid_extensions"] = valid_extensions
        return cleaned

    def validate_smart_open_files(self, cleaned_data):
        smartopen_file_fields = [
            "base_file_path",
            "dbf_file_path",
            "shx_file_path",
            "prj_file_path",
            "xml_file_path",
            "sld_file_path",
        ]
        for file_field in smartopen_file_fields:
            value = cleaned_data.get(file_field, None)
            if value and isinstance(value, str):
                cleaned_data[file_field] = smart_open.parse_uri(value)

    def validate_files_sum_of_sizes(self):
        max_size = self._get_uploads_max_size()
        total_size = self._get_uploaded_files_total_size()
        if total_size > max_size:
            raise forms.ValidationError(_(
                f'Total upload size exceeds {filesizeformat(max_size)}. Please try again with smaller files.'
            ))

    def _get_uploads_max_size(self):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug="total_upload_size_sum")
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit()
        return max_size_db_obj.max_size

    def _get_uploaded_files(self):
        """Return a list with all of the uploaded files"""
        return [django_file for field_name, django_file in self.files.items()
                if field_name != "base_file"]

    def _get_files_paths(self):
        """Return a list with all of the uploaded files"""
        files_paths = (
            self.cleaned_data.get("dbf_file_path", None),
            self.cleaned_data.get("shx_file_path", None),
            self.cleaned_data.get("prj_file_path", None),
            self.cleaned_data.get("xml_file_path", None),
            self.cleaned_data.get("sld_file_path", None),
        )
        return [url for url in files_paths if url]

    def get_uploaded_or_smartopen_files_paths(self):
        """Return a list with all of the uploaded files"""
        files_paths = (
            self.cleaned_data.get("base_file_path", None),
            self.cleaned_data.get("dbf_file_path", None),
            self.cleaned_data.get("shx_file_path", None),
            self.cleaned_data.get("prj_file_path", None),
            self.cleaned_data.get("xml_file_path", None),
            self.cleaned_data.get("sld_file_path", None),
        )
        all_file_paths = [smartopen_file.uri_path for smartopen_file in files_paths if smartopen_file]
        # Todo: Finish
        # [django_file.name for django_file in self.files.values()]
        # [django_file.path for django_file in self.files.values()]
        return all_file_paths

    def _get_uploaded_files_total_size(self):
        """Return a list with all of the uploaded files"""
        excluded_files = ("zip_file", "shp_file", )
        uploaded_files_sizes = [
            django_file.size for field_name, django_file in self.files.items()
            if field_name not in excluded_files
        ]
        total_size = sum(uploaded_files_sizes)
        return total_size


class TimeForm(forms.Form):
    presentation_strategy = forms.CharField(required=False)
    precision_value = forms.IntegerField(required=False)
    precision_step = forms.ChoiceField(required=False, choices=[
        ('years',) * 2,
        ('months',) * 2,
        ('days',) * 2,
        ('hours',) * 2,
        ('minutes',) * 2,
        ('seconds',) * 2
    ])

    def __init__(self, *args, **kwargs):
        # have to remove these from kwargs or Form gets mad
        self._time_names = kwargs.pop('time_names', None)
        self._text_names = kwargs.pop('text_names', None)
        self._year_names = kwargs.pop('year_names', None)
        super().__init__(*args, **kwargs)
        self._build_choice('time_attribute', self._time_names)
        self._build_choice('end_time_attribute', self._time_names)
        self._build_choice('text_attribute', self._text_names)
        self._build_choice('end_text_attribute', self._text_names)
        widget = forms.TextInput(attrs={'placeholder': 'Custom Format'})
        if self._text_names:
            self.fields['text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
            self.fields['end_text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
        self._build_choice('year_attribute', self._year_names)
        self._build_choice('end_year_attribute', self._year_names)

    def _resolve_attribute_and_type(self, *name_and_types):
        return [(self.cleaned_data[n], t) for n, t in name_and_types
                if self.cleaned_data.get(n, None)]

    def _build_choice(self, att, names):
        if names:
            names.sort()
            choices = [('', '<None>')] + [(a, a) for a in names]
            self.fields[att] = forms.ChoiceField(
                choices=choices, required=False)

    @property
    def time_names(self):
        return self._time_names

    @property
    def text_names(self):
        return self._text_names

    @property
    def year_names(self):
        return self._year_names

    def clean(self):
        starts = self._resolve_attribute_and_type(
            ('time_attribute', 'Date'),
            ('text_attribute', 'Text'),
            ('year_attribute', 'Number'),
        )
        if len(starts) > 1:
            raise ValidationError('multiple start attributes')
        ends = self._resolve_attribute_and_type(
            ('end_time_attribute', 'Date'),
            ('end_text_attribute', 'Text'),
            ('end_year_attribute', 'Number'),
        )
        if len(ends) > 1:
            raise ValidationError('multiple end attributes')
        if len(starts) > 0:
            self.cleaned_data['start_attribute'] = starts[0]
        if len(ends) > 0:
            self.cleaned_data['end_attribute'] = ends[0]
        return self.cleaned_data

    # @todo implement clean


class SRSForm(forms.Form):
    source = forms.CharField(required=True)

    target = forms.CharField(required=False)


def _supported_type(ext, supported_types):
    return any([type_.matches(ext) for type_ in supported_types])
