import datetime
import json

import requests
# from fcm_django.models import FCMDevice
"""

from app.settings import FCM_DJANGO_SETTINGS

from core.models import ContactFCM
from customer.models import CustomerFCM

FCM_SERVER_KEY = FCM_DJANGO_SETTINGS.get('FCM_SERVER_KEY')


def send_fcm_push_notification_appointment(contact_id, type, status, table_no=0, msg=''):
    status_value = {
        "Received": {
            'notification': {'title': 'Received',
                             'body': f'An order has been placed {str(datetime.datetime.now())}'},
            'data': {'title': '1', 'body': str(datetime.datetime.now())}
        },
        'Cooking': {
            'notification': {'title': 'Cooking',
                             'body': f'Your food is preparing {str(datetime.datetime.now())}'},
            'data': {'title': '2', 'body': str(datetime.datetime.now())}
        },
        'WaiterHand': {
            'notification': {'title': 'WaiterHand',
                             'body': f'Your food is ready for serving {str(datetime.datetime.now())}'},
            'data': {'title': '3', 'body': str(datetime.datetime.now())}
        },
        'Delivered': {
            'notification': {'title': 'Delivered',
                             'body': f'Food has been delivered {str(datetime.datetime.now())}'},
            'data': {'title': '5', 'body': str(datetime.datetime.now())}
        },
        'Rejected': {
            'notification': {'title': 'Rejected',
                             'body': f'Your food is rejected by kitchen {str(datetime.datetime.now())}'},
            'data': {'title': '6', 'body': str(datetime.datetime.now())}
        },
        'CallStaff': {
            'notification': {'title': 'Calling Waiter',
                             'body': f'Customer from table no {str(table_no)} is looking for you'},
            'data': {'title': '7', 'body': str(datetime.datetime.now())}
        },
        'CallStaffForPayment': {
            'notification': {'title': 'Calling Waiter for payment',
                             'body': f'Customer from table no {str(table_no)} is looking for you for {str(msg)} payment'},
            'data': {'title': '8', 'body': str(datetime.datetime.now())}
        },
    }
    try:
        if type == 'customer':
            device = CustomerFCM.objects.filter(customer=contact_id).first()
        else:
            device = ContactFCM.objects.filter(customer=contact_id).first()
        if device:
            fcm_token = device.fcm_token
            data = {
                "notification": status_value[status]['notification'],
                "data": status_value[status]['data'],
                "to": fcm_token
            }
            headers = {
                'Content-type': 'application/json',
                'Authorization': 'key=' + str(FCM_SERVER_KEY)
            }
            response = requests.post(
                'https://fcm.googleapis.com/fcm/send', data=json.dumps(data), headers=headers)
            # print("Fcm Response ", response)
            if 300 > response.status_code >= 200:
                if response.json().get('failure') < 1:
                    return True
            return False
        else:
            return False

    except Exception as e:
        print("FCm Exception ", e)
"""
