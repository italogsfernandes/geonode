import io
import logging

from django.core.management import (
    get_commands,
    load_command_class
)

logger = logging.getLogger(__name__)


def get_management_commands():
    """
    Get the list of all management commands, filter by the attr injected by the
    decorator and returns a dict with the app and command class.
    """
    available_commands = {}
    mngmt_commands = get_commands()

    for name, app_name in mngmt_commands.items():
        # Load command
        try:
            command_class = load_command_class(app_name, name)
        except (ImportError, AttributeError) as exception:
            logging.info(
                f'Command "{name}" from app "{app_name}" cannot be listed or ' f'used by http, exception: "{exception}"'
            )
            continue

        # Verify if its exposed
        is_exposed = hasattr(command_class, "expose_command_over_http") and command_class.expose_command_over_http
        if is_exposed:
            available_commands[name] = {
                "app": app_name,
                "command_class": command_class,
            }

    return available_commands


def get_management_command_details(command_class):
    """
    Get the help output of the management command.
    """
    with io.StringIO() as output:
        command_class.print_help(output)
        cmd_help_output = output.getvalue()
    return cmd_help_output
