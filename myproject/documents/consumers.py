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
            "pdf_viewer_group",
            {
                "type": "pdf_viewer_message",
                "message": data
            }
        )

    def pdf_viewer_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
