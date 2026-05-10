from twilio.rest import Client
from django.conf import settings

def send_sms(to_phone: str, message: str):
    """
    Send SMS to a customer using Twilio.
    """
    if not to_phone:
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        return True
    except Exception as e:
        print("Error sending SMS:", e)
        return False
