from django.shortcuts import redirect
from django.conf import settings

class UnilabSetupMiddleware:
    """
    Middleware that checks if the application's database has been configured.
    If settings.IS_CONFIGURED is False, it redirects all requests to /setup, 
    bypassing only static files, setup APIs, and the setup page itself.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Bypass static files, setup views, and setup APIs
        if (path.startswith('/static/') or 
            path.startswith('/api/setup') or 
            path == '/setup'):
            return self.get_response(request)

        if not getattr(settings, 'IS_CONFIGURED', False):
            return redirect('/setup')

        return self.get_response(request)
