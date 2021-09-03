from django.apps import AppConfig


class MngmtCommandsHttpAppConfig(AppConfig):
    name = 'geonode.mngmt_commands_http'
    verbose_name = "Management Commands Over HTTP"


default_app_config = 'geonode.mngmt_commands_http.MngmtCommandsHttpAppConfig'
