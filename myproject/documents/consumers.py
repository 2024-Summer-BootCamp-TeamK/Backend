# documents/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.document_group_name = f'document_{self.document_id}'

        # Join document group
        await self.channel_layer.group_add(
            self.document_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave document group
        await self.channel_layer.group_discard(
            self.document_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']
        payload = data['payload']

        # Send message to document group
        await self.channel_layer.group_send(
            self.document_group_name,
            {
                'type': f'document_{message_type}',
                'payload': payload
            }
        )

    # Receive message from document group
    async def document_scroll(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'scroll',
            'payload': payload
        }))
