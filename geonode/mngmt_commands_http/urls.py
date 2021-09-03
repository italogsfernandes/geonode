from django.urls import re_path
from .views import ManagementCommandView


urlpatterns = [
    re_path(r'management/$', ManagementCommandView.as_view()),
    re_path(r'management/(?P<cmd_name>\w+)/$', ManagementCommandView.as_view()),
]

# TODO: ManagementCommandsJobs ApiView
# * management/cmd_name/jobs/ (GET (list), GET (detail), POST (create) and PATCH (execute/cancel))