
import channels.layers
from asgiref.sync import async_to_sync
from restaurant.serializers import FoodOrderByTableSerializer, TableStaffSerializer
from restaurant.models import FoodOrder, Table


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


def socket_fire_task_on_order_crud(restaurant_id, order_id, state, data):
    # print("runnign task from task.py")
    response_data = {}

    # staff_list = HotelStaffInformation.objects.filter(
    #     restaurant_id=restaurant_id,).values_list('pk', flat=True)
    staff_list = Table.objects.filter(restaurant_id=restaurant_id,
                                    food_orders__id=order_id).order_by('table_no').distinct().values_list('staff_assigned__pk', flat=True)
    # staff_list = list(table_qs.values_list('staff_assigned__pk', flat=True))

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
            qs = Table.objects.filter(
                restaurant_id=restaurant_id,
                staff_assigned=staff_id).order_by('table_no')
            serializer = TableStaffSerializer(instance=qs, many=True)
            async_to_sync(layer.group_send)(
                waiter_group_name, {'type': 'response_to_listener', 'data': serializer.data})

        # print('done')
    except:
        pass
    # print('signal got a call', order_qs, table_qs, state)
