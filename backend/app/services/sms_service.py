import africastalking

# Initialize Africa's Talking // sandbox details
AT_USERNAME = "your_at_username"
AT_API_KEY = "your_at_api_key"

africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

def send_sms_alert(phone_number: str, message: str, sender_id: str = None):
    """
    Sends an SMS using Africa's Talking.
    Phone numbers must be in E.164 format (e.g., +254712345678).
    """
    try:
        # If the phone number lacks the country code, format it for Kenya
        if phone_number.startswith("0"):
            phone_number = "+254" + phone_number[1:]
        elif phone_number.startswith("254"):
            phone_number = "+" + phone_number
            
        kwargs = {
            "to": [phone_number],
            "message": message
        }
        if sender_id:
            kwargs["from_"] = sender_id # e.g., "MOBILINK"
            
        response = sms.send(**kwargs)
        return response
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {str(e)}")
        return None