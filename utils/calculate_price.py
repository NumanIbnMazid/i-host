import decimal
from restaurant.models import *
import restaurant
from django.utils import timezone


def calculate_price(food_order_obj, include_initial_order=False, **kwargs):
    if include_initial_order:
        ordered_items_qs = food_order_obj.ordered_items.exclude(
            status__in=["4_CANCELLED"])
    else:
        ordered_items_qs = food_order_obj.ordered_items.exclude(
            status__in=["4_CANCELLED", "0_ORDER_INITIALIZED"])

    restaurant_qs = food_order_obj.restaurant
    promo_code = food_order_obj.applied_promo_code  # kwargs.get('promo_code')
    cash_received = food_order_obj.cash_received
    discount_given= food_order_obj.discount_given
    if promo_code:
        parent_promo_code_promotion_qs = ParentCompanyPromotion.objects.filter(
            code=promo_code,  restaurant=restaurant_qs, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
        if parent_promo_code_promotion_qs:
            parent_promo_qs = parent_promo_code_promotion_qs
        else:
            promo_code_promotion_qs = PromoCodePromotion.objects.filter(
                code=promo_code, restaurant=restaurant_qs, start_date__lte=timezone.now(),
                end_date__gte=timezone.now()).first()
            parent_promo_qs = promo_code_promotion_qs


    else:
        parent_promo_qs = None
    # if food_order_obj.table:
    #     restaurant_qs = food_order_obj.table.restaurant

    total_price = 0.0
    tax_amount = 0.0
    grand_total_price = 0.0
    service_charge = 0.0
    hundred = 100.0
    discount_amount = 0.0

    for ordered_item in ordered_items_qs:

        if not restaurant_qs:
            restaurant_qs = ordered_item.food_option.food.restaurant
        item_price = ordered_item.quantity*ordered_item.food_option.price
        extra_price = ordered_item.quantity * sum(
            list(
                ordered_item.food_extra.values_list('price', flat=True)
            )
        )
        if ordered_item.food_option.food.discount:
            discount_amount += (ordered_item.food_option.food.discount.amount/100)*item_price

        total_price += item_price+extra_price
    grand_total_price += total_price

    if restaurant_qs.service_charge_is_percentage:
        service_charge = (restaurant_qs.service_charge*total_price / hundred)
    else:
        service_charge = restaurant_qs.service_charge

    if parent_promo_qs:
        promo_discount_amount = 0

        if parent_promo_qs.promo_type == "PERCENTAGE":
            promo_discount_amount = grand_total_price * \
                (parent_promo_qs.amount/100)
        else:
            promo_discount_amount = parent_promo_qs.amount

        if grand_total_price < parent_promo_qs.minimum_purchase_amount:
            promo_discount_amount = 0

        discount_amount += promo_discount_amount
        if discount_amount > parent_promo_qs.max_amount:
            discount_amount = parent_promo_qs.max_amount

    if discount_given:
        discount_amount = 0


        if food_order_obj.discount_amount_is_percentage == True:
            discount_amount = grand_total_price * \
                                    (discount_given / 100)
        else:
            discount_amount = discount_given

    grand_total_price += service_charge
    tax_amount = ((total_price * restaurant_qs.tax_percentage)/hundred)
    grand_total_price += tax_amount
    # if discount_given:
    #     payable_amount = grand_total_price - discount_amount
    payable_amount = grand_total_price - discount_amount
    if cash_received==None or cash_received <=0:
        cash_received = 0
        change_amount = 0

    # else cash_received >= 0:
    else:
        change_amount = 0.0
        if cash_received>payable_amount:
            change_amount = cash_received - payable_amount
        food_order_obj.change_amount = change_amount
        food_order_obj.save()
    # else:
    #     cash_received = 0
    #     change_amount = 0



    response_dict = {
        "grand_total_price": round(grand_total_price, 2),
        'discount_amount': round(discount_amount, 2),
        'payable_amount': round(payable_amount, 2),
        "tax_amount": round(tax_amount, 2),
        'tax_percentage': round(restaurant_qs.tax_percentage, 2),
        "service_charge": round(service_charge, 2),
        "service_charge_is_percentage": restaurant_qs.service_charge_is_percentage,
        "service_charge_base_amount": restaurant_qs.service_charge,
        'total_price': round(total_price, 2),
        'cash_received':cash_received,
        'change_amount':round(change_amount,2),
    }
    food_order_obj.grand_total_price = response_dict.get('grand_total_price')
    food_order_obj.total_price = response_dict.get('total_price')
    food_order_obj.discount_amount = response_dict.get('discount_amount')
    food_order_obj.tax_amount = response_dict.get('tax_amount')
    food_order_obj.tax_percentage = response_dict.get('tax_percentage')
    food_order_obj.service_charge = response_dict.get('service_charge')
    food_order_obj.payable_amount = response_dict.get('payable_amount')
    food_order_obj.save()

    return response_dict


def calculate_item_price_with_discount(ordered_item_qs):
    total_price = 0.0
    discount_amount = 0.0
    item_price = ordered_item_qs.quantity*ordered_item_qs.food_option.price
    if ordered_item_qs.food_option.food.discount:
        discount_amount = (
            ordered_item_qs.food_option.food.discount.amount/100)*item_price
    total_price += item_price
    total_price = total_price-discount_amount
    extra_price = ordered_item_qs.quantity*sum(
        list(
            ordered_item_qs.food_extra.values_list('price', flat=True)
        )
    )
    total_price += extra_price

    return round(total_price, 2)
