from django.http import HttpResponseForbidden
from .models import BannedIP


class IPBanMiddleware:
    """
    Blocks banned IPs at the HTTP layer too.
    Add to MIDDLEWARE in settings.py BEFORE other middlewares:

        'videochat.middleware.IPBanMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_ip(request)
        if BannedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden(
                "<h1>403 – You have been permanently banned.</h1>"
                "<p>Your IP address has been blocked due to a violation of community guidelines.</p>"
            )
        return self.get_response(request)

    @staticmethod
    def _get_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")