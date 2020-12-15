import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from channels.generic.websocket import AsyncWebsocketConsumer


class RestaurantOrderListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('-----------------hello----------------')
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.group_name = 'restaurant_%s' % self.restaurant_id

        # Join room group
        # async_to_sync(self.channel_layer.group_add)(
        #     self.room_group_name,
        #     self.channel_name
        # )

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # async_to_sync(self.channel_layer.group_discard)(
        #     self.room_group_name,
        #     self.channel_name
        # )

        await self.channel_layer.group_discart(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'message': message
        #     }
        # )
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
