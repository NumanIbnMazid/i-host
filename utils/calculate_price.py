import decimal
from restaurant.models import *
import restaurant
from django.utils import timezone
from datetime import date, datetime, timedelta


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
    take_away_discount_given = food_order_obj.take_away_discount_given
    remove_discount = food_order_obj.remove_discount
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
    sd_charge_amount = 0.0
    grand_total_price = 0.0
    service_charge = 0.0
    hundred = 100.0
    discount_amount = 0.0
    total_price_without_vat=0.0
    total_price_with_vat=0.0
    take_away_discount_amount = 0.0
    total_take_away_discount = 0.0
    without_discount_food_price = 0.0
    base_remove_discount_amount = 0.0

    for ordered_item in ordered_items_qs:

        if not restaurant_qs:
            restaurant_qs = ordered_item.food_option.food.restaurant
        item_price = ordered_item.quantity*ordered_item.food_option.price
        extra_price = ordered_item.quantity * sum(
            list(
                ordered_item.food_extra.values_list('price', flat=True)
            )
        )

        discount_id = ordered_item.food_option.food.discount
        if discount_id:
            today = timezone.datetime.now().date()
            start_date = today + timedelta(days=1)

            current_time = timezone.now()

            date_wise_discount_qs = Discount.objects.filter(pk = discount_id.id, restaurant=food_order_obj.restaurant_id,
                                                  start_date__lte=start_date,end_date__gte=today,discount_schedule_type='Date_wise').exclude(food=None, image=None)
            time_wise_discount_qs = Discount.objects.filter(pk = discount_id.id, restaurant_id = food_order_obj.restaurant_id,discount_slot_closing_time__gte = current_time,
                                                            discount_slot_start_time__lte =current_time, discount_schedule_type='Time_wise').exclude(food=None, image=None)
            if date_wise_discount_qs or time_wise_discount_qs:
                # discount_amount += (ordered_item.food_option.food.discount.amount/100)*item_price
                without_discount_food_price = (ordered_item.food_option.food.discount.amount/100)*item_price
                discount_amount+=without_discount_food_price

        if discount_given and not discount_id:
            if food_order_obj.discount_amount_is_percentage:
                discount_amount +=(discount_given/100)*item_price
            # else:
            #     discount_amount += discount_given

        if take_away_discount_given:
            if discount_id:
                food_price_with_discount = item_price - without_discount_food_price
            else:
                food_price_with_discount =  item_price
            if food_order_obj.take_away_discount_amount_is_percentage:
                take_away_discount_amount = (take_away_discount_given*food_price_with_discount)/100
                total_take_away_discount += take_away_discount_amount
                discount_amount+=take_away_discount_amount

            else:
                discount_amount+=take_away_discount_given


        if parent_promo_qs and not discount_id:
            promo_discount_amount = 0
            if parent_promo_qs.promo_type == "PERCENTAGE":
                promo_discount_amount = item_price * (parent_promo_qs.amount / 100)
            else:
                promo_discount_amount = parent_promo_qs.amount*ordered_item.quantity
            discount_amount += promo_discount_amount


        total_price += item_price+extra_price


        if ordered_item.food_option.food.is_vat_applicable:
            total_price_with_vat += item_price+extra_price
        else:
            total_price_without_vat+= item_price+extra_price

    if discount_given and not discount_id:
        if not food_order_obj.discount_amount_is_percentage:
            discount_amount = discount_given
    grand_total_price += total_price

    # if remove_discount:
    #     if food_order_obj.remove_discount_amount_is_percentage:
    #         base_remove_discount_amount = remove_discount * discount_amount / 100
    #     else:
    #         base_remove_discount_amount = remove_discount
    #     discount_amount -= base_remove_discount_amount

    if food_order_obj.restaurant.is_vat_charge_apply_in_original_food_price \
            and food_order_obj.restaurant.is_service_charge_apply_in_original_food_price:

        if restaurant_qs.service_charge_is_percentage:
            service_charge = (restaurant_qs.service_charge*total_price / hundred)
        else:
            service_charge = restaurant_qs.service_charge

        grand_total_price += service_charge

        # ------!!!!!!-----Vat Apply Only Vat Applicable Food ------!!!!!!-----

        tax_amount = ((total_price_with_vat * restaurant_qs.tax_percentage)/hundred)
        sd_charge_amount = ((total_price * restaurant_qs.sd_charge_percentage)/hundred)
        grand_total_price += tax_amount
        # if discount_given:
        #     payable_amount = grand_total_price - discount_amount

        #------!!!!---- REMOVE DISCOUNT------!!!!----
        # if remove_discount:
        #     if food_order_obj.remove_discount_amount_is_percentage:
        #         base_remove_discount_amount = remove_discount*discount_amount/100
        #     else:
        #         base_remove_discount_amount = remove_discount
        #     discount_amount -= base_remove_discount_amount

        payable_amount = grand_total_price - discount_amount
        # total_price-=discount_amount


    else:
        total_food_price = total_price
        total_price -= discount_amount


        if restaurant_qs.service_charge_is_percentage:
            service_charge = (restaurant_qs.service_charge * total_price / hundred)
        else:
            service_charge = restaurant_qs.service_charge


        total_price += service_charge
        # tax_amount = ((total_price * restaurant_qs.tax_percentage) / hundred)
        total_price_with_vat +=service_charge
        tax_amount = total_price_with_vat * restaurant_qs.tax_percentage / hundred


        payable_amount = total_price+ tax_amount
        total_price = total_food_price
        grand_total_price = payable_amount + discount_amount


    if cash_received==None or cash_received <=0:
        cash_received = 0
        change_amount = 0

    # else cash_received >= 0:
    else:
        change_amount = 0.0
        if cash_received>payable_amount:
            change_amount = cash_received - payable_amount
        food_order_obj.change_amount = change_amount
        food_order_obj.take_away_discount_base_amount = total_take_away_discount
        food_order_obj.save()


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
    # Discount is valid or not check
    today = timezone.datetime.now().date()
    start_date = today + timedelta(days=1)
    current_time = timezone.now()

    if ordered_item_qs.food_option.food.discount:
        discount_id = ordered_item_qs.food_option.food.discount_id
        if discount_id:
            date_wise_discount_qs = Discount.objects.filter(pk = discount_id, restaurant_id=ordered_item_qs.food_option.food.restaurant_id,
                                                            start_date__lte=start_date, end_date__gte=today,
                                                            discount_schedule_type='Date_wise').exclude(food=None,
                                                                                                        image=None)
            time_wise_discount_qs = Discount.objects.filter(pk = discount_id, restaurant_id=ordered_item_qs.food_option.food.restaurant_id,
                                                            discount_slot_closing_time__gte=current_time,
                                                            discount_slot_start_time__lte=current_time,
                                                            discount_schedule_type='Time_wise').exclude(food=None,
                                                                                                        image=None)
            if date_wise_discount_qs or time_wise_discount_qs:
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
