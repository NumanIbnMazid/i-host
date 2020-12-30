import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Table, FoodOrder
from channels.generic.websocket import AsyncWebsocketConsumer
from .serializers import FoodOrderByTableSerializer
from channels.db import database_sync_to_async


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # print('-----------------connect----------------')
        self.restaurant_id = int(self.scope.get(
            'url_route', {}).get('kwargs', {}).get('restaurant_id'))
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
        """
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']

        # Send message to room group
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'message': message
        #     }
        # )
        """
        if text_data:
            # data = await self.order_item_list(restaurant_id=int(text_data))
            data = async_to_sync(self.order_item_list(
                restaurant_id=int(text_data)))

        else:
            data = {'error': ['restaurant id invalid']}
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'response_to_listener',
                'data': data
            }
        )

    # @database_sync_to_async
    def order_item_list(self, restaurant_id):

        qs = FoodOrder.objects.filter(table__restaurant=restaurant_id).exclude(
            status__in=['5_PAID', '6_CANCELLED']).order_by('table_id')
        ordered_table_set = set(qs.values_list('table_id', flat=True))
        table_qs = Table.objects.filter(
            restaurant=restaurant_id).exclude(pk__in=ordered_table_set).order_by('id')
        empty_table_data = []
        for empty_table in table_qs:
            empty_table_data.append(
                {
                    'table': empty_table.pk,
                    'table_no': empty_table.table_no,
                    'table_name': empty_table.name,
                    'status': '',
                    'price': {},
                    'ordered_items': []
                }
            )
        serializer = FoodOrderByTableSerializer(instance=qs, many=True)
        response_data = serializer.data+empty_table_data
        return response_data if response_data else ['from consumer order_item_list', str(restaurant_id)]

    # async def chat_message(self, event):
    #     message = event['message']

    #     # Send message to WebSocket
    #     await self.send(text_data=json.dumps({
    #         'message': message
    #     }))

    async def response_to_listener(self, event):
        data = event.get('data')
        restaurant_id = event.get('restaurant_id')
        response_data = {}
        # print('---------------response to listener--------------')
        state = event.get('state')
        # response_data = await self.order_item_list(restaurant_id=int(restaurant_id))
        response_data = async_to_sync(
            self.order_item_list(restaurant_id=int(restaurant_id)))

        # UNCOMMENT IN FUTURE
        # if state in ['data_only']:
        #     if not data:
        #         response_data = await self.order_item_list(restaurant_id=restaurant_id)
        #     else:
        #         response_data = data
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'data': response_data
            # 'test': 'test success',
        }))
