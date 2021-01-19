from account_management.models import HotelStaffInformation
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Table, FoodOrder
from channels.generic.websocket import AsyncWebsocketConsumer
from .serializers import FoodOrderByTableSerializer, TableStaffSerializer
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
            data = await self.order_item_list(restaurant_id=int(text_data))
        else:
            data = {'error': ['restaurant id invalid']}
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'response_to_listener',
                'data': data
            }
        )

    @database_sync_to_async
    def order_item_list(self, restaurant_id=1):

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
        return serializer.data+empty_table_data

    # async def chat_message(self, event):
    #     message = event['message']

    #     # Send message to WebSocket
    #     await self.send(text_data=json.dumps({
    #         'message': message
    #     }))

    async def response_to_listener(self, event):
        data = event['data']
        # print('---------------response to listener--------------')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'data': data
            # 'test': 'test success',
        }))


class AppsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # print('-----------------connect----------------')
        self.waiter_id = int(self.scope.get(
            'url_route', {}).get('kwargs', {}).get('waiter_id'))
        # await self.set_table_ids()

        self.group_name = 'waiter_%s' % self.waiter_id
        # '_'.join(map(str, self.table_ids))

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

    @database_sync_to_async
    def set_table_ids(self):
        staff_qs = HotelStaffInformation.objects.filter(
            pk=self.waiter_id).first()
        if staff_qs:
            self.table_ids = list(staff_qs.restaurant.tables.values_list(
                'pk', flat=True).order_by('pk'))
        else:
            self.table_ids = []

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
            data = await self.order_item_list(waiter_id=int(text_data))
        else:
            data = {'error': ['restaurant id invalid']}
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'response_to_listener',
                'data': data
            }
        )

    @database_sync_to_async
    def order_item_list(self, waiter_id: int, single_table=False):
        qs = Table.objects.filter(
            staff_assigned=waiter_id).order_by('table_no')
        # qs = Table.objects.filter(pk__in=table_ids).order_by('table_no')
        # qs = FoodOrder.objects.filter(table_id__in=table_ids).exclude(
        #     status__in=['5_PAID', '6_CANCELLED']).order_by('table_id')
        # ordered_table_set = set(qs.values_list('table_id', flat=True))
        # table_qs = Table.objects.filter(
        #     pk__in=table_ids).exclude(pk__in=ordered_table_set).order_by('id')
        # empty_table_data = []
        # if single_table:
        #     serializer = FoodOrderByTableSerializer(instance=qs)
        #     return serializer.data

        # for empty_table in table_qs:
        #     empty_table_data.append(
        #         {
        #             'table': empty_table.pk,
        #             'table_no': empty_table.table_no,
        #             'table_name': empty_table.name,
        #             'status': '',
        #             'price': {},
        #             'ordered_items': []
        #         }
        #     )
        serializer = TableStaffSerializer(instance=qs, many=True)
        return serializer.data

    # async def chat_message(self, event):
    #     message = event['message']

    #     # Send message to WebSocket
    #     await self.send(text_data=json.dumps({
    #         'message': message
    #     }))

    async def response_to_listener(self, event):
        data = event['data']
        # print('---------------response to listener--------------')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'data': data
            # 'test': 'test success',
        }))
