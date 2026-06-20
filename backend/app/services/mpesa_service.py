import base64
from datetime import datetime, timezone
import httpx
from typing import Optional, Tuple

class DarajaService:
    def __init__(self, consumer_key: str, consumer_secret: str, shortcode: str, passkey: str, env: str = "sandbox"):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        
        # Base URLs for Safaricom Daraja
        if env == "production":
            self.base_url = "https://api.safaricom.co.kr/mpesa" # Production URL
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"  # Sandbox URL

        # Internal token cache memory to respect rate limits
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    async def _get_oauth_token(self) -> str:
        """
        Generates and returns a valid Safaricom OAuth Access Token.
        Utilizes internal caching to minimize external API calls.
        """
        import time
        # Check if cached token is still valid (with a 60-second safety buffer)
        if self._access_token and self._token_expires_at and time.time() < (self._token_expires_at - 60):
            return self._access_token

        # Generate basic auth string
        keys_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_keys = base64.b64encode(keys_string.encode("utf-8")).decode("utf-8")
        
        headers = {"Authorization": f"Basic {encoded_keys}"}
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Cache the new token details
                self._access_token = data["access_token"]
                # Safaricom tokens typically last 3600 seconds (1 hour)
                self._token_expires_at = time.time() + int(data["expires_in"])
                
                return self._access_token
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Daraja OAuth Authentication Failed: {e.response.text}")
            except Exception as e:
                raise RuntimeError(f"Network error during Daraja OAuth: {str(e)}")

    def _generate_timestamp_and_password(self) -> Tuple[str, str]:
        """
        Generates the specialized cryptographic timestamp and password string 
        required for Lipa Na M-Pesa Online (STK Push).
        Format: Base64(Shortcode + Passkey + Timestamp)
        """
        # Format must be exactly YYYYMMDDHHmmss in East Africa Time (or UTC equivalent offset)
        # Daraja strictly expects 14 characters
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        
        raw_password = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(raw_password.encode("utf-8")).decode("utf-8")
        
        return timestamp, password

    async def initiate_stk_push(
        self, 
        phone_number: str, 
        amount: int, 
        callback_url: str, 
        account_reference: str, 
        transaction_desc: str
    ) -> dict:
        """
        Triggers an M-Pesa STK Push request to a customer's phone handset.
        
        :param phone_number: Format must be 2547XXXXXXXX or 2541XXXXXXXX
        :param amount: Whole integer value in KSh
        :param callback_url: Secure HTTPS API endpoint hosted on your FastAPI server
        :param account_reference: Visible label to user (e.g., WiFi Account Number)
        :param transaction_desc: Internal text describing intent
        """
        token = await self._get_oauth_token()
        timestamp, password = self._generate_timestamp_and_password()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline", # CustomerBuyGoodsOnline for Till Numbers
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        url = f"{self.base_url}/mpesa/stkpush/v1/query" if False else f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                response_data = response.json()
                
                # Check for successful handshake from Safaricom (ResponseCode '0' means request accepted)
                if response_data.get("ResponseCode") == "0":
                    return {
                        "success": True,
                        "merchant_request_id": response_data.get("MerchantRequestID"),
                        "checkout_request_id": response_data.get("CheckoutRequestID"),
                        "description": response_data.get("ResponseDescription")
                    }
                else:
                    return {
                        "success": False,
                        "error": response_data.get("ResponseDescription", "Unknown Daraja rejection error")
                    }
            except httpx.HTTPStatusError as e:
                return {"success": False, "error": f"Safaricom Server Error: {e.response.text}"}
            except Exception as e:
                return {"success": False, "error": f"Connection Failure: {str(e)}"}