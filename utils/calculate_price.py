import decimal


def calculate_price(food_order_obj):
    ordered_items_qs = food_order_obj.ordered_items.exclude(
        status__in=["4_CANCELLED", "0_ORDER_INITIALIZED"])

    restaurant_qs = None
    if food_order_obj.table:
        restaurant_qs = food_order_obj.table.restaurant

    total_price = decimal.Decimal(0.0)
    tax_amount = decimal.Decimal(0.0)
    grand_total_price = decimal.Decimal(0.0)
    service_charge = decimal.Decimal(0.0)
    hundred = decimal.Decimal(100.0)
    for ordered_item in ordered_items_qs:
        if not restaurant_qs:
            restaurant_qs=ordered_item.food_option.food.restaurant
        item_price = ordered_item.quantity*ordered_item.food_option.price
        extra_price = ordered_item.quantity * sum(
            list(
                ordered_item.food_extra.values_list('price', flat=True)
            )
        )
        total_price += item_price+extra_price
    grand_total_price += total_price
    
    

    if restaurant_qs.service_charge_is_percentage:
        service_charge = grand_total_price * \
            (restaurant_qs.service_charge/hundred)
    else:
        service_charge = grand_total_price + \
            restaurant_qs.service_charge
    grand_total_price += service_charge
    tax_amount = grand_total_price * (restaurant_qs.tax_percentage/hundred)
    grand_total_price += tax_amount
    return {"grand_total_price": grand_total_price, "tax_amount": tax_amount, "service_charge": service_charge, 'total_price': grand_total_price}
