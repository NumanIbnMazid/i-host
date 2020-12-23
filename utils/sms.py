import requests
from django.utils import timezone
from django.conf import settings

def send_sms(body='test_sms', phone="01921317475"):
    sms_data = {
        'api_token': settings.SSL_SMS_API_TOKEN, "sid": "IHOSTMASKING", "sms": body, "msisdn": phone, "csms_id": "35434029384"+timezone.now().date().__str__()}
    req = requests.post(
        url="https://smsplus.sslwireless.com/api/v3/send-sms", data=sms_data)
    if req.status_code == 200:
        return True

    return False
