import restaurant
from account_management.models import HotelStaffInformation
import base64
import json
from django_q.tasks import async_task

import channels.layers
from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings
from django.dispatch import Signal, receiver
from django.template.loader import render_to_string
from django.utils import timezone
from utils.print_node import print_node
from weasyprint import CSS, HTML

from restaurant.models import Table
from restaurant.serializers import (FoodOrderByTableSerializer,
                                    OrderedItemTemplateSerializer, TableStaffSerializer)

from .models import FoodOrder

order_done_signal = Signal(
    providing_args=["qs", "data", "state"])

kitchen_items_print_signal = Signal(
    providing_args=["qs"])


def order_item_list(restaurant_id=1):
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


@receiver(order_done_signal)
def socket_fire_on_order_change_signals(sender,   restaurant_id, order_id=None, qs=None, data=None, state='data_only', **kwargs):
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
    async_task('restaurant.tasks.socket_fire_task_on_order_crud',
               restaurant_id, order_id, state, data)
    # socket_fire_task_on_order_crud(restaurant_id, order_id, state, data)


def socket_fire_task_on_order_crud(restaurant_id, order_id, state, data):
    response_data = {}
    # staff_list = HotelStaffInformation.objects.filter(
    #     restaurant_id=restaurant_id,).values_list('pk', flat=True)
    table_qs = Table.objects.filter(restaurant_id=restaurant_id,
                                    food_orders__id=order_id).prefetch_related('food_orders').order_by('table_no').distinct()
    staff_list = list(table_qs.values_list('staff_assigned__pk', flat=True))

    if state in ['data_only']:
        if not data:
            data = order_item_list(restaurant_id)
        response_data = data

    layer = channels.layers.get_channel_layer()
    try:
        group_name = 'restaurant_%s' % int(restaurant_id)

        async_to_sync(layer.group_send)(
            group_name, {'type': 'response_to_listener', 'data': response_data})
        for staff_id in staff_list:
            waiter_group_name = 'waiter_%s' % staff_id
            qs = table_qs.filter(
                staff_assigned=staff_id).order_by('table_no')
            serializer = TableStaffSerializer(instance=qs, many=True)
            async_to_sync(layer.group_send)(
                waiter_group_name, {'type': 'response_to_listener', 'data': serializer.data})

        # print('done')
    except:
        pass
    # print('signal got a call', order_qs, table_qs, state)


@receiver(kitchen_items_print_signal)
def kitchen_items_print(sender, qs=None, *args, **kwargs):
    # items_qs = OrderedItem.objects.all().exclude(food_extra=None)
    serializer = OrderedItemTemplateSerializer(
        instance=qs, many=True)
    context = {
        'table_no': qs.values_list('food_order__table__table_no', flat=True).distinct().last(),
        'order_id': qs.values_list('food_order__order_no', flat=True).distinct().last(),
        'date': str(timezone.now().strftime('%d/%m/%Y')),
        'time': str(timezone.now().strftime("%I:%M %p")),
        'items_data': serializer.data
    }
    html_string = render_to_string('invoice.html', context)
    # @page { size: Letter; margin: 0cm }
    css = CSS(
        string='@page { size: 80mm 350mm; margin: 0mm }')
    pdf_byte_code = HTML(string=html_string).write_pdf(
        stylesheets=[
            css], zoom=1
    )
    pdf_obj_encoded = base64.b64encode(pdf_byte_code)
    pdf_obj_encoded = pdf_obj_encoded.decode('utf-8')
    print_node(pdf_obj=pdf_obj_encoded,restaurant_id = qs.last().food_order.restaurant_id)
