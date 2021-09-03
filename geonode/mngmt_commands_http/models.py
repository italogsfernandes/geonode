from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


def default_storage():
    return {'args': [], 'kwargs': {}}



class ManagementCommandJob(models.Model):
    """
    Stores the requests to run a management command using this app.
    It allows us to have more control over the celery TaskResults.
    TODO: Add a CeleryTaskResult FK field and show it as as link on the admin.
         it is also needed in order to stop/change the celery execution.
    TODO: stop_task method
    TODO: Tests
    """
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    STATUS_CHOICES = (
        (CREATED, _("Created")),
        (QUEUED, _("Queued")),
        (RUNNING, _("Running")),
        (SUCCESS, _("Success")),
        (FAILED, _("Failed")),
    )
    command = models.CharField(max_length=250, null=False)
    app_name = models.CharField(max_length=250, null=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    modified_at = models.DateTimeField(auto_now=True)

    # TODO: Asks about django 3.1 and JsonField (a better fit for this field)
    args = models.TextField(null=True)
    kwargs = models.TextField(null=True)

    output_message = models.TextField(null=True)

    status = models.CharField(
        choices=STATUS_CHOICES,
        default=CREATED,
        max_length=max([len(e[0]) for e in STATUS_CHOICES]),
    )

    def __str__(self):
        return f"{self.command} run by {self.user} on  {self.created_at}"

    def start_task(self):
        """
        Start the task.
        """
        from .tasks import run_management_command_async
        self.status = self.QUEUED
        self.save()
        return run_management_command_async.delay(job_id=self.id)


    def stop_task(self, soft_stop):
        """
        Sends a soft stop to the task.
        """
        pass