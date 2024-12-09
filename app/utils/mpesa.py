import requests
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from flask import current_app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MpesaCredentials:
    """Data class to hold M-Pesa API credentials"""
    consumer_key: str
    consumer_secret: str
    shortcode: str
    environment: str = 'production'
    passkey: Optional[str] = None
    stk_push_shortcode: Optional[str] = None
    stk_push_passkey: Optional[str] = None

class MpesaAuthManager:
    """Handles M-Pesa API authentication"""
    
    def __init__(self, credentials: MpesaCredentials):
        self.credentials = credentials
        self._access_token = None
        self._token_expiry = None

        # Base URLs for different environments
        if credentials.environment == 'sandbox':
            self.auth_url = 'https://sandbox.safaricom.co.ke/oauth'
            self.api_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.auth_url = 'https://api.safaricom.co.ke/oauth'
            self.api_url = 'https://api.safaricom.co.ke'

    def get_access_token(self) -> str:
        """Generate or retrieve cached OAuth access token"""
        try:
            # Check if token exists and is not expired
            if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
                logger.debug("Using cached access token")
                return self._access_token

            # Clear any existing token
            self._access_token = None
            self._token_expiry = None

            auth_url = f'{self.auth_url}/v1/generate?grant_type=client_credentials'
            auth_string = f'{self.credentials.consumer_key}:{self.credentials.consumer_secret}'
            auth_base64 = base64.b64encode(auth_string.encode()).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            logger.info(f"Getting new access token from: {auth_url}")
            logger.debug(f"Using credentials: consumer_key={self.credentials.consumer_key[:4]}***, environment={self.credentials.environment}")
            
            response = requests.get(
                auth_url,
                headers=headers,
                verify=True,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Auth failed: {response.status_code} - {response.text}")
                raise ValueError(f"Authentication failed: {response.text}")
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                raise ValueError("Invalid JSON response from auth endpoint")

            self._access_token = data.get('access_token')
            
            if not self._access_token:
                logger.error(f"No access token in response: {data}")
                raise ValueError("No access token in response")
            
            # Set token expiry (typically 1 hour)
            expires_in = int(data.get('expires_in', 3599))
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 100)  # Buffer of 100 seconds
            
            logger.info("Successfully obtained new access token")
            logger.debug(f"Token expiry set to: {self._token_expiry}")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            # Clear token on error
            self._access_token = None
            self._token_expiry = None
            raise

class MpesaC2B:
    """Handles M-Pesa Customer to Business (C2B) operations"""
    
    def __init__(self):
        """Initialize with credentials from Flask config"""
        credentials = MpesaCredentials(
            consumer_key=current_app.config['MPESA_CONSUMER_KEY'],
            consumer_secret=current_app.config['MPESA_CONSUMER_SECRET'],
            shortcode=current_app.config['MPESA_SHORTCODE'],
            environment=current_app.config.get('MPESA_ENVIRONMENT', 'production'),
            passkey=current_app.config.get('MPESA_PASSKEY'),
            stk_push_shortcode=current_app.config.get('MPESA_STK_PUSH_SHORTCODE'),
            stk_push_passkey=current_app.config.get('MPESA_STK_PUSH_PASSKEY')
        )
        self.auth_manager = MpesaAuthManager(credentials)
        self.api_url = self.auth_manager.api_url
        self.credentials = credentials

    def register_urls(
        self,
        confirmation_url: str,
        validation_url: str,
        response_type: str = "Completed"
    ) -> Dict[str, Any]:
        """Register confirmation and validation URLs for C2B payments
        
        Args:
            confirmation_url (str): The URL that receives the confirmation request
            validation_url (str): The URL that receives the validation request
            response_type (str): Response type for the validation request
            
        Returns:
            Dict[str, Any]: Response from the M-Pesa API
        """
        url = f'{self.api_url}/mpesa/c2b/v1/registerurl'
        
        payload = {
            "ShortCode": self.credentials.shortcode,
            "ResponseType": response_type,
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
        }
        
        try:
            logger.info(f"Registering URL with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully registered URL: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"URL registration failed: {str(e)}")
            logger.error(f"Response content: {getattr(e.response, 'text', '')}")
            raise

    def initiate_payment(
        self,
        amount: int,
        phone_number: str,
        bill_ref_number: str,
        command_id: str = "CustomerPayBillOnline"
    ) -> Dict[str, Any]:
        """Initiate a C2B payment request"""
        try:
            # Format phone number (remove leading 0 or +254)
            if phone_number.startswith('+254'):
                phone_number = phone_number[4:]
            elif phone_number.startswith('0'):
                phone_number = phone_number[1:]
            phone_number = '254' + phone_number

            # Generate timestamp and password
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            # Get callback URL from config, fallback to constructed URL
            callback_url = current_app.config.get('MPESA_STK_CALLBACK_URL')
            if not callback_url:
                callback_url = f"{current_app.config['MPESA_CALLBACK_BASE_URL']}/payments/stk/callback"
            
            # Remove any trailing slashes
            callback_url = callback_url.rstrip('/')
            
            # Remove /v1 if present in the path
            callback_url = callback_url.replace('/v1/', '/').replace('/v1', '/')
            
            url = f'{self.api_url}/mpesa/stkpush/v1/processrequest'
            payload = {
                "BusinessShortCode": self.credentials.stk_push_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": int(phone_number),
                "PartyB": self.credentials.stk_push_shortcode,
                "PhoneNumber": int(phone_number),
                "CallBackURL": callback_url,
                "AccountReference": bill_ref_number,
                "TransactionDesc": "Payment for TabPay"
            }
        
            # Get a fresh token for each request
            access_token = self.auth_manager.get_access_token()
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            logger.info(f"Initiating payment to URL: {url}")
            logger.info(f"Using callback URL: {callback_url}")
            logger.info(f"Initiating payment with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=30,
                verify=True
            )
            
            if response.status_code != 200:
                logger.error(f"Payment request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully initiated payment: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initiating payment: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            raise

    def generate_password(self, timestamp: str) -> str:
        """Generate password for STK Push"""
        if self.credentials.environment == 'sandbox':
            business_short_code = "174379"
            passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        else:
            business_short_code = self.credentials.stk_push_shortcode
            passkey = self.credentials.stk_push_passkey
            
        password_str = f"{business_short_code}{passkey}{timestamp}"
        return base64.b64encode(password_str.encode()).decode('utf-8')

    def initiate_stk_push(
        self,
        phone_number: str,
        amount: int,
        account_reference: str,
        transaction_desc: str = "Payment for TabPay"
    ) -> Dict[str, Any]:
        """Initiate STK Push payment request"""
        if not self.credentials.stk_push_shortcode or not self.credentials.stk_push_passkey:
            raise ValueError("STK Push credentials not configured")

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)
        
        url = f'{self.api_url}/mpesa/stkpush/v1/processrequest'
        
        # Format phone number (add 254 prefix if needed)
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
            
        payload = {
            "BusinessShortCode": self.credentials.stk_push_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.credentials.stk_push_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": current_app.config.get('MPESA_STK_CALLBACK_URL'),
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
        }
        
        try:
            logger.info(f"Initiating STK Push with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"STK Push request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully initiated STK Push: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initiating STK Push: {str(e)}")
            logger.error(f"Response content: {getattr(e.response, 'text', '')}")
            raise

    def query_stk_push_status(
        self,
        checkout_request_id: str,
    ) -> Dict[str, Any]:
        """Query the status of an STK Push transaction"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)
        
        url = f'{self.api_url}/mpesa/stkpushquery/v1/query'
        
        payload = {
            "BusinessShortCode": self.credentials.stk_push_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
        }
        
        try:
            logger.info(f"Querying STK Push status with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"STK Push status query failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully queried STK Push status: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying STK Push status: {str(e)}")
            logger.error(f"Response content: {getattr(e.response, 'text', '')}")
            raise

# Create a singleton instance
mpesa_client = None

def get_mpesa_client() -> MpesaC2B:
    """Get or create the M-Pesa client singleton"""
    global mpesa_client
    if mpesa_client is None:
        mpesa_client = MpesaC2B()
    return mpesa_client
