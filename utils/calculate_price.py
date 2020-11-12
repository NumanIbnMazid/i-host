import decimal


def calculate_price(food_order_obj):
    ordered_items_qs = food_order_obj.ordered_items.exclude(
        status__in=["5_PAID", "6_CANCELLED", "0_ORDER_INITIALIZED"])

    total_price = decimal.Decimal(0.0)
    tax_amount = decimal.Decimal(0.0)
    grand_total_price = decimal.Decimal(0.0)
    service_charge = decimal.Decimal(0.0)
    for ordered_item in ordered_items_qs:
        item_price = ordered_item.quantity*ordered_item.food_option.price
        extra_price = ordered_item.quantity * sum(
            list(
                ordered_item.food_extra.values_list('price', flat=True)
            )
        )
        total_price += item_price+extra_price
    grand_total_price += total_price
    if food_order_obj.table.restaurant.service_charge_is_percentage:
        service_charge = grand_total_price * \
            food_order_obj.table.restaurant.service_charge/100
    else:
        service_charge = grand_total_price + \
            food_order_obj.table.restaurant.service_charge
    grand_total_price += service_charge
    tax_amount = grand_total_price * food_order_obj.table.restaurant.tax_percentage/100
    grand_total_price += tax_amount
    return {"grand_total_price": grand_total_price, "tax_amount": tax_amount, "service_charge": service_charge, 'total_price': grand_total_price}
