import io

from rest_framework import status, views
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

from .models import ManagementCommandJob
from .utils import create_command_parser
from .serializers import ManagementCommandJobSerializer

from rest_framework import permissions
from django.core.management import call_command, get_commands,find_commands, load_command_class

import logging
import json

logger = logging.getLogger(__name__)


def get_management_command_list():
    """
    TODO: move to utils.py, usecases.py or repositories.py....
    TODO: UPDATE: should return name, app_name and also the loaded class.
    """
    mngmt_commands = get_commands()
    available_commands = []
    for name, app_name in mngmt_commands.items():
        try:
            command_class = load_command_class(app_name, name)
        except (ImportError, AttributeError) as exception:
            logging.warning(f'Command "{name}" from app "{app_name}" cannot be listed or used by http, exception: "{exception}"')
            continue
        if hasattr(command_class, "__expose_command_over_http__") and command_class.__expose_command_over_http__:
            available_commands.append({"name": name, "app_name": app_name})

    return available_commands




class ManagementCommandView(views.APIView):
    """
    * GET List of exposed commands
    * GET Help for a specific command
    * POST create a job (and automatic runs) for a specific command.
    TODO: Automatic run as a body argument, serializer (jsonfield) for args and kwargs.
    TODO: Verify with proposal with all the API endpoints are implemented.
    TODO: Refactor to a easier to read code / separate web stuff from domain/bussiness rules stuff.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, cmd_name=None, format=None):
        available_commands = get_management_command_list()

        # --- handle list case ---
        if cmd_name is None:
            # queryset = ManagementCommand.objects.filter(expose=True)
            return Response({'success': True, 'error': None, 'commands': available_commands})

        # --- handle detail case ---
        # check if Management Command is exposed
        is_available = any(cmd_obj['name'] == 'sleep_some_minutes' for cmd_obj in available_commands)
        if not is_available:
            return Response({'success': False, 'error': 'Command not found'}, status=status.HTTP_404_NOT_FOUND)

        # fetch help text of the Command
        parser = create_command_parser(cmd_name)
        with io.StringIO() as output:
            parser.print_help(output)
            logged_output = output.getvalue()

        return Response({'success': True, 'error': None, 'data': logged_output})

    def post(self, request, cmd_name=None):
        """
        Method handling command execution order. Expects application/json content type in a following shape:
        {
            "args": [<arg1>, <arg2>],
            "kwargs: {<key1>: <val1>, <key2>: <val2>}
        }
        """
        available_commands = get_management_command_list()

        # --- handle list case ---
        if cmd_name is None:
            return Response({'success': False, 'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # --- handle detail case ---
        # check if Management Command is exposed
        is_available = any(cmd_obj['name'] == 'sleep_some_minutes' for cmd_obj in available_commands)
        if not is_available:
            return Response({'success': False, 'error': 'Command not found'}, status=status.HTTP_404_NOT_FOUND)

        args = request.data.get('args', [])
        kwargs = request.data.get('kwargs', {})

        if "--help" in args:
            return Response({'success': False, 'error': 'Forbidden argument: "--help"', 'log': None},
                            status=status.HTTP_400_BAD_REQUEST)

        job_data = {
            "command": cmd_name,
            "app_name": [cmd_obj["app_name"] for cmd_obj in available_commands if cmd_obj['name'] == 'sleep_some_minutes'][0],
            "user": self.request.user,
            "args": json.dumps(args),
            "kwargs": json.dumps(kwargs),
            "status": ManagementCommandJob.CREATED,
        }

        job = ManagementCommandJob.objects.create(**job_data)
        celery_task = job.start_task()

        response = {
            'success': True,
            'error': None,
            'data': ManagementCommandJobSerializer(instance=job).data
        }

        return Response(response)
