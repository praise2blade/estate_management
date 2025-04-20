import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Assign group name based on the user id
        self.group_name = f"estate_notifications_{self.scope['user'].id}"
        
        # Join the user's specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group when disconnected
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # This can handle messages sent from the WebSocket (optional for custom messages)
        data = json.loads(text_data)
        # In this case, we forward the message to the resident's group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_notification',
                'message': data['message'],
            }
        )

    async def send_notification(self, event):
        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))

