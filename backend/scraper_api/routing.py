from django.urls import re_path
from . import consumers

# This tells Channels which consumer to use for a given WebSocket URL
websocket_urlpatterns = [
    re_path(r'ws/search/$', consumers.SearchConsumer.as_asgi()),
]

