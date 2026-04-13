import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from matchmaking.routing import websocket_urlpatterns  # ← ye change karo

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # ← ye bhi check karo

application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})