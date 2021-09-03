from django.core.management.base import BaseCommand
from time import sleep
from geonode.mngmt_commands_http.decorators import expose_command_over_http


@expose_command_over_http
class Command(BaseCommand):
    help = 'Do nothing, sleeps for X minutes'

    def add_arguments(self, parser):
        parser.add_argument('minutes', nargs='+', type=float)

    def handle(self, *args, **options):
        minute = options['minutes'][0]
        self.stdout.write(f"Sleeping for {minute} minutes")
        total_minutes = minute
        total_seconds = minute * 60.0
        while total_seconds > 0:
            self.stdout.write(f"Remaining time: {total_minutes:2.0f} min {(int(total_seconds)%60):.1f} s", ending='\r')
            self.stdout.flush()
            total_seconds -= 1
            total_minutes = int(total_seconds / 60)
            sleep(1)
        self.stdout.write(f"Remaining time: {total_minutes:2.0f} min {(int(total_seconds)%60):.1f} s")
        self.stdout.write(self.style.SUCCESS("Successfully executed!"))