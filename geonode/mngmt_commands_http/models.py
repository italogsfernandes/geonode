from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models


class ManagementCommandJob(models.Model):
    """
    Stores the requests to run a management command using this app.
    It allows us to have more control over the celery TaskResults.
    """

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    FINISHED = "FINISHED"
    STATUS_CHOICES = (
        (CREATED, "Created"),
        (QUEUED, "Queued"),
        (STARTED, "Started"),
        (FINISHED, "Finished"),
    )
    command = models.CharField(max_length=250, null=False)
    app_name = models.CharField(max_length=250, null=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    modified_at = models.DateTimeField(auto_now=True)

    # NOTE: Change to JsonField when updating to django 3.1
    args = models.TextField(null=True)
    kwargs = models.TextField(null=True)

    celery_result_id = models.UUIDField(null=True, blank=True)
    output_message = models.TextField(null=True)

    status = models.CharField(
        choices=STATUS_CHOICES,
        default=CREATED,
        max_length=max([len(e[0]) for e in STATUS_CHOICES]),
    )

    def __str__(self):
        return (
            f"ManagementCommandJob"
            f"({self.id}, {self.command}, {self.user}, {self.created_at})"
        )

    def start_task(self):
        from .tasks import run_management_command_async

        if self.status != self.CREATED:
            raise exceptions.BadRequest
        self.status = self.QUEUED
        self.save()
        run_management_command_async.delay(job_id=self.id)

    def stop_task(self):
        from geonode.celery_app import app as celery_app

        celery_app.control.terminate(self.celery_result_id)

    @property
    def celery_task_meta(self):
        from .tasks import run_management_command_async

        if not self.celery_result_id:
            return None
        async_result = run_management_command_async.AsyncResult(self.celery_result_id)
        task_meta = async_result.backend.get_task_meta(self.celery_result_id)
        return task_meta
