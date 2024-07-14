# documents/consumers.py

import json
from channels.generic.websocket import WebsocketConsumer

class DocumentConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        self.channel_layer.group_send(
            "document_%s" % self.scope['url_route']['kwargs']['document_id'],
            {
                "type": "document.message",
                "message": data
            }
        )

    def document_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
