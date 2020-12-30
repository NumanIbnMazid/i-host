from restaurant.serializers import FoodOrderByTableSerializer
from django.dispatch import Signal, receiver
from asgiref.sync import async_to_sync, sync_to_async
import channels.layers
from channels.generic.websocket import JsonWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.conf import settings

from restaurant.models import Table
from .models import (
    FoodOrder)


order_done_signal = Signal(
    providing_args=["qs", "data", "state"])


def order_item_list(restaurant_id):
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
    return response_data if response_data else ['from signal order_item_list']


@receiver(order_done_signal)
def dashboard_update_on_order_change_signals(sender,   restaurant_id, qs=None, data=None, state='data_only', **kwargs):
    """
    signal reciever for dashboard update and call websocket connections

    Parameters
    ----------
    sender : signal sender ref

    order_qs : queryset
        Order
    table_qs : queryset
        Table
    state : str
        [data_only]
    """
    if settings.TURN_OFF_SIGNAL:
        return
    # print('---------------------------------------------------------------------------------------------------------------')
    # print("FIRING Signals")
    # print('---------------------------------------------------------------------------------------------------------------')
    response_data = {}
    # if state in ['data_only']:
    #     if not data:
    #         data = order_item_list(restaurant_id)
    #     response_data = data

    layer = channels.layers.get_channel_layer()
    try:
        group_name = 'restaurant_%s' % int(restaurant_id)

        # sync_to_async(layer.group_send)(group_name), {
        #     'type': 'send_message_to_frontend',
        #     'data': response_data,

        # })
        async_to_sync(layer.group_send)(
            group_name, {'type': 'response_to_listener', 'data': response_data, "restaurant_id": restaurant_id, "state": state, 'qs': qs})

        # layer.group_send(
        #     str(res_id),
        #     {
        #         'type': 'send_message_to_frontend',
        #         'message': message,
        #     }
        # )
        # print('done')
    except:
        pass
    # print('signal got a call', order_qs, table_qs, state)
