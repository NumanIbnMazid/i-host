from ..models import FoodOrder


def generate_order_no(restaurant_id: int, order_qs: FoodOrder = None):
    last_order_no = ""
    DIGITS_FOR_ORDER = 6
    if order_qs:
        last_order_qs = FoodOrder.objects.filter(
            restaurant_id=restaurant_id).exclude(pk=order_qs.pk).order_by('-created_at').first()
    else:
        last_order_qs = FoodOrder.objects.filter(
            restaurant_id=restaurant_id).order_by('-created_at').first()
    last_order_no = last_order_qs.order_no
    if last_order_no == None:
        last_order_no = str(0).zfill(DIGITS_FOR_ORDER)

    try:
        order_no = str(int(last_order_no)+1).zfill(DIGITS_FOR_ORDER)
    except:
        order_no = str(0).zfill(DIGITS_FOR_ORDER)
    return order_no
