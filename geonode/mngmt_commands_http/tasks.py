from celery import shared_task
from .utils import run_management_command



@shared_task(
    bind=True,
    name='geonode.mngmt_commands_http.tasks.run_management_command_async',
    ignore_result=False,
)
def run_management_command_async(self, job_id):
    """
    Celery Task responsible to run the management command.
    It justs sends the `job_id` arg to a function that gonna call
    `django.core.management.call_command` with all the required setup.
    """
    run_management_command(job_id, async_result_id=self.request.id)

