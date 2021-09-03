import io
import sys
import json

from .models import ManagementCommandJob
from django.utils import timezone
from django.core.management import (
    call_command, BaseCommand, get_commands, CommandError, load_command_class
)

class JobRunner:
    """
    With-statement context used to execute a ManagementCommandJob.
    It handles status, start_time and end_time.
    And duplicates stdout and stderr to a specified file stream.
    """
    def __init__(self, job, stream: io.StringIO):
        self.job = job
        self.stream = stream

        self.stdout = sys.stdout
        self.stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self
      
    def write(self, data):
        self.stream.write(data)
        self.stdout.write(data)

    def flush(self):
        self.stream.flush()

    def __enter__(self):
        self.job.status = ManagementCommandJob.RUNNING
        self.job.start_time = timezone.now()
        self.job.save()
        return self.job
  
    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        if exc_type:
            self.job.status = ManagementCommandJob.FAILED
        else:
            self.job.status = ManagementCommandJob.SUCCESS
        self.job.end_time = timezone.now()
        self.job.output_message = self.stream.getvalue()
        self.job.save()



def run_management_command(job_id):
    """
    Loads the job model from database and run it using `call_command` inside a
    context responsible to updating the status and redirecting stdout and 
    stderr.
    TODO: Write Test
    """
    job = ManagementCommandJob.objects.get(id=job_id)
    with io.StringIO() as output:
        with JobRunner(job, output):
            job_args = json.loads(job.args)
            job_kwargs = json.loads(job.kwargs)
            call_command(job.command, *job_args, **job_kwargs, stdout=output)


#################
# TO BE DELETED #
#################
def create_command_parser(command_name):
    """
    Function creating argument parser for a management command
    TODO: Delete, no need for this parser.
    """
    if isinstance(command_name, BaseCommand):
        # Command object passed in.
        command = command_name
        command_name = command.__class__.__module__.split('.')[-1]
    else:
        # Load the command object by name.
        try:
            app_name = get_commands()[command_name]
        except KeyError:
            raise CommandError("Unknown command: %r" % command_name)

        if isinstance(app_name, BaseCommand):
            # If the command is already loaded, use it directly.
            command = app_name
        else:
            command = load_command_class(app_name, command_name)

    return command.create_parser('', command_name)

