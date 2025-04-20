from twilio.rest import Client
from django.conf import settings
import random
import string

def send_sms(visitor_request):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    body = (
        f"Hello {visitor_request.visitor_name}, your visitor code is: {visitor_request.unique_code}. "
        f"It expires: {visitor_request.expires_at.strftime('%Y-%m-%d %H:%M')}."
    )

    try:
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=visitor_request.phone_number
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)



def generate_unique_code():
    """Generate a random 10-character alphanumeric code."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(10))
