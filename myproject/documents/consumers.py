import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['documentId']
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
        await self.channel_layer.group_send(
            self.document_group_name,
            {
                "type": "document_message",
                "message": data
            }
        )

    async def document_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
