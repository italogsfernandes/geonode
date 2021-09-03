from django.contrib import admin
from .models import ManagementCommandJob


@admin.register(ManagementCommandJob)
class ManagementCommandJobAdmin(admin.ModelAdmin):
    """
    Allow us to see the Jobs on admin, and (re-)execute a job if needed.
    TODO: Action to cancel a job and allow to create a new one. 
    """
    list_display = (
        "command",
        "app_name",
        "user",
        "args",
        "kwargs",
        "created_at",
        "start_time",
        "end_time",
        "modified_at",
        "status",
    )
    list_filter = ("command", "app_name", "user")
    list_per_page = 20

    search_fields = ("command", "app_name", "user")
    readonly_fields = (
        "command",
        "app_name",
        "user",
        "created_at",
        "start_time",
        "end_time",
        "modified_at",
        "status",
        "args",
        "kwargs",
        "output_message",
    )
    actions = ["execute"]

    def execute(self, request, queryset):
        for job in queryset.iterator():
            job.start_task()

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
