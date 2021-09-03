from django.urls import re_path

from .views import ManagementCommandView

urlpatterns = [
    re_path(r"management/$", ManagementCommandView.as_view()),
    re_path(r"management/(?P<cmd_name>\w+)/$", ManagementCommandView.as_view()),
]
