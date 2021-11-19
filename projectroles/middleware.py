import cProfile
import sys

from io import StringIO

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class ProfilerMiddleware(MiddlewareMixin):
    """
    cProfile based profiling middleware.
    Based on: https://djangosnippets.org/snippets/727/
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler.create_stats()
            out = StringIO()
            old_stdout, sys.stdout = sys.stdout, out
            self.profiler.print_stats(1)
            sys.stdout = old_stdout
            response.content = '<pre>{}</pre>'.format(out.getvalue())
        return response
