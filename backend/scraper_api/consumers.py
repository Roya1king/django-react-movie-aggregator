# File: backend/scraper_api/consumers.py

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import SiteSource
from .tasks import scrape_site # This is our one and only task

# --- Database and Celery calls ---
# We still need this for the database call
@sync_to_async
def get_active_sites():
    # We use list() to force the database query to execute now
    return list(SiteSource.objects.filter(is_active=True))

# --- Consumer ---

class SearchConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        """Called when the WebSocket is handshaking."""
        await self.accept()
        print(f"WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """Called when the WebSocket closes."""
        print(f"WebSocket disconnected: {self.channel_name}")

    async def receive_json(self, content):
        """
        Called when we get a message from React/Postman.
        This is the trigger for the search.
        """
        action = content.get('action')
        
        if action == 'search':
            term = content.get('term')
            if not term:
                await self.send_error_message_to_client("No search term provided.")
                return

            print(f"Starting search for: {term}")
            
            # Call our async-safe database function
            active_sites = await get_active_sites()
            
            if not active_sites:
                await self.send_error_message_to_client("No active sites configured in admin.")
                return

            for site in active_sites:
                # --- THIS IS NOW SIMPLER ---
                # Just send the job! No need to check for queues.
                scrape_site.delay(site.id, term, self.channel_name)
                # --- END SIMPLER CODE ---

    # --- These methods are called BY the channel layer ---

    async def send_search_result(self, event):
        """
        Handler for the 'send_search_result' event from a task.
        Sends the final data back to React/Postman.
        """
        await self.send_json(event['result']) # Send the 'result' dictionary

    async def send_error_message(self, event):
        """
        Handler for the 'send_error_message' event from a task.
        """
        await self.send_error_message_to_client(event['message'])

    async def send_error_message_to_client(self, message):
        """Helper to send a JSON-formatted error to the client."""
        await self.send_json({
            'error': True,
            'message': message
        })