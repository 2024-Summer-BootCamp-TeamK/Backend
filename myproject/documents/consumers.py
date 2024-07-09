import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.document_group_name = f'document_{self.document_id}'

        await self.channel_layer.group_add(
            self.document_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.document_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        pointer_position = data['pointer_position']

        await self.channel_layer.group_send(
            self.document_group_name,
            {
                'type': 'pointer_position',
                'pointer_position': pointer_position
            }
        )

    async def pointer_position(self, event):
        pointer_position = event['pointer_position']

        await self.send(text_data=json.dumps({
            'pointer_position': pointer_position
        }))
