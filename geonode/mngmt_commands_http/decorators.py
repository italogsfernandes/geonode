class expose_command_over_http:
    """
    - Add this decorator @expose_command_over_http to the BaseCommand
    (django.core.management.base.BaseCommand) you want to expose over http.
    - It will inject the attribute "expose_command_over_http" that is used to
    determine wherever the Command should be exposed or not.
    """
    def __init__(self, inner_object):
        self.inner_object = inner_object
        self.inner_object.expose_command_over_http = True

    def __call__(self, *args, **kwargs):
        return self.inner_object(*args, **kwargs)
