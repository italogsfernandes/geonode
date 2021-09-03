from rest_framework import permissions, status, views
from rest_framework.response import Response

from .utils import get_management_command_details, get_management_commands


class ManagementCommandView(views.APIView):
    """
    Handle the exposed management commands usage:
      - GET: List of exposed commands
      - GET detail: Help for a specific command
      - POST: Create a job (and automatic runs) for a specific command.
    """

    permission_classes = [permissions.IsAdminUser]
    allowed_methods = ["GET", "POST"]

    def retrieve_details(self, cmd_name):
        # Object not found
        if cmd_name not in self.available_commands:
            return Response(
                {"success": False, "error": "Command not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Object Details: fetch help text of the Command
        cmd_details = get_management_command_details(
            self.available_commands[cmd_name]["command_class"]
        )
        return Response({"success": True, "error": None, "data": cmd_details})

    def list(self):
        return Response({
            "success": True,
            "error": None,
            "data": self.available_commands.keys()
        })

    def get(self, request, cmd_name=None):
        self.available_commands = get_management_commands()
        # List
        if cmd_name is None:
            return self.list()
        # Retrieve
        return self.retrieve_details(cmd_name)
