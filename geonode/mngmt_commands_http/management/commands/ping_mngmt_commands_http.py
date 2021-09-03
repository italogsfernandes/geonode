from time import sleep
from django.core.management.base import BaseCommand
from geonode.mngmt_commands_http.decorators import expose_command_over_http


@expose_command_over_http
class Command(BaseCommand):
    help = 'It writes "pong" to stdout.'

    def add_arguments(self, parser):
        parser.add_argument("--sleep", nargs="?", const=1, type=float)
        parser.add_argument("--force_exception", nargs="?", type=bool)

    def handle(self, *args, **options):
        if options["sleep"]:
            seconds_to_sleep = options["sleep"]
            self.stdout.write(f"Sleeping for {seconds_to_sleep} seconds...")
            sleep(seconds_to_sleep)
        if options["force_exception"]:
            self.stdout.write(
                self.style.ERROR("As requested, an exception will be raised.")
            )
            raise RuntimeError("User Requested Exception")
        self.stdout.write(self.style.SUCCESS("pong"))
