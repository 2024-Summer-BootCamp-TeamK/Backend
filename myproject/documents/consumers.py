import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.document_group_name = f'document_{self.document_id}'

        # Join document group
        await self.channel_layer.group_add(
            self.document_group_name,
            self.channel_name
        )

        # 사용자 카운트 증가 및 할당
        self.username = await self.get_username()

        await self.accept()

        # Send initial user count and username
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'payload': {'username': self.username}
        }))

    async def disconnect(self, close_code):
        # Leave document group
        await self.channel_layer.group_discard(
            self.document_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def get_username(self):
        # Redis나 Django Cache를 이용한 사용자 수 관리
        key = f'document_{self.document_id}_user_count'
        user_count = cache.get(key, 0) + 1
        cache.set(key, user_count, None)
        return str(user_count)

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
    async def document_mouse_move(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'mouse_move',
            'payload': payload
        }))

    async def document_page_change(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'page_change',
            'payload': payload
        }))

    # 서명 추가 이벤트 처리
    async def document_add_drawing(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'add_drawing',
            'payload': payload
        }))

    # 서명 업데이트 이벤트 처리
    async def document_update_drawing(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'update_drawing',
            'payload': payload
        }))

    # 서명 삭제 이벤트 처리
    async def document_delete_drawing(self, event):
        payload = event['payload']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'delete_drawing',
            'payload': payload
        }))
