from django.contrib import admin

from .models import ManagementCommandJob


@admin.register(ManagementCommandJob)
class ManagementCommandJobAdmin(admin.ModelAdmin):
    """
    Allow us to see the Jobs on admin, and (re-)execute a job if needed.
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
        "status",
        "celery_result_id",
    )
    list_filter = ("command", "app_name", "user")
    list_per_page = 20

    search_fields = ("command", "app_name", "user", "celery_result_id")
    readonly_fields = (
        "celery_result_id",
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
        "celery_state",
        "celery_traceback",
    )
    actions = ["execute", "stop"]

    def execute(self, request, queryset):
        for job in queryset.iterator():
            job.start_task()

    def stop(self, request, queryset):
        for job in queryset.iterator():
            job.stop_task()

    def celery_state(self, instance):
        return instance.celery_task_meta.get("status")

    def celery_traceback(self, instance):
        return instance.celery_task_meta.get("traceback")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
