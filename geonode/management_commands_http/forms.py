from django import forms

from geonode.management_commands_http.models import ManagementCommandJob

from geonode.management_commands_http.utils.commands import (
    get_management_commands,
)

from geonode.management_commands_http.utils.jobs import (
    start_task,
)


class ManagementCommandJobAdminForm(forms.ModelForm):
    autostart = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["command"] = forms.ChoiceField(
            choices=[(command, command) for command in get_management_commands()]
        )

    def save(self, commit=True):
        # import ipdb; ipdb.set_trace()
        instance = super().save(commit)
        # autostart = self.cleaned_data.get("autostart", False)
        if commit:
            print("form save with commit enabled")
        return instance


    class Meta:
        model = ManagementCommandJob
        fields = ("command", "args", "kwargs",)

