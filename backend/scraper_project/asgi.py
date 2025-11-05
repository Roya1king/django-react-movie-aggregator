import os
from django.core.asgi import get_asgi_application

# Set the DJANGO_SETTINGS_MODULE environment variable *first*.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper_project.settings')

# Call get_asgi_application() here. This is the crucial part.
# It runs django.setup() and configures all the settings.
django_asgi_app = get_asgi_application()

# --- Now that Django is set up, we can safely import our app ---
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import scraper_api.routing

# This is the application that Daphne will run
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Use the variable we just created
    "websocket": AuthMiddlewareStack(
        AuthMiddlewareStack(
            URLRouter(
                scraper_api.routing.websocket_urlpatterns
            )
        )
    ),
})
