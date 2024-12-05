import requests
import base64
import json
import logging
from datetime import datetime
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
        # Base URLs for different environments
        self.auth_url = 'https://sandbox.safaricom.co.ke/oauth' if credentials.environment == 'sandbox' else 'https://api.safaricom.co.ke/oauth'
        self.api_url = 'https://sandbox.safaricom.co.ke' if credentials.environment == 'sandbox' else 'https://api.safaricom.co.ke'
        self._access_token = None

    def get_access_token(self) -> str:
        """Generate or retrieve cached OAuth access token"""
        if not self._access_token:
            auth_url = f'{self.auth_url}/v1/generate'
            auth_string = f'{self.credentials.consumer_key}:{self.credentials.consumer_secret}'
            auth_base64 = base64.b64encode(auth_string.encode()).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_base64}',
                'Cache-Control': 'no-cache'
            }
            
            params = {
                'grant_type': 'client_credentials'
            }
            
            try:
                logger.info(f"Attempting to get access token from: {auth_url}")
                # logger.debug(f"Using auth string: {auth_string}")
                logger.debug(f"Using credentials - Consumer Key: {self.credentials.consumer_key[:5]}... Consumer Secret: {self.credentials.consumer_secret[:5]}...")
                logger.debug(f"Using auth header: Basic {auth_base64[:20]}...")
                
                with requests.Session() as session:
                    response = session.get(
                        auth_url,
                        headers=headers,
                        params=params,
                        verify=True,
                        timeout=60
                    )
                
                if response.status_code != 200:
                    logger.error(f"Authentication failed with status {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    response.raise_for_status()
                
                response_data = response.json()
                logger.debug(f"Token response data: {json.dumps(response_data, indent=2)}")
                
                self._access_token = response_data.get('access_token')
                if not self._access_token:
                    raise ValueError("No access token in response")
                    
                logger.info("Successfully generated access token")
                logger.debug(f"Access token (first 20 chars): {self._access_token[:20]}...")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error generating access token: {str(e)}")
                raise
            except ValueError as e:
                logger.error(f"Error parsing access token: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during authentication: {str(e)}")
                raise
        
        return self._access_token

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
        if self.credentials.environment == 'sandbox':
            url = f'{self.api_url}/mpesa/c2b/v1/simulate'
            payload = {
                "ShortCode": self.credentials.shortcode,
                "CommandID": command_id,
                "Amount": int(amount),
                "Msisdn": str(phone_number),
                "BillRefNumber": bill_ref_number
            }
        else:
            # In production, we use STK Push
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            # Format phone number (remove leading 0 or +254)
            if phone_number.startswith('+254'):
                phone_number = phone_number[4:]
            elif phone_number.startswith('0'):
                phone_number = phone_number[1:]
            phone_number = '254' + phone_number
            
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
                "CallBackURL": current_app.config['MPESA_STK_CALLBACK_URL'],
                "AccountReference": bill_ref_number,
                "TransactionDesc": "Payment for TabPay"
            }
        
        # Get a fresh token for each request
        access_token = self.auth_manager.get_access_token()
        logger.debug(f"Using access token (first 20 chars) for payment request: {access_token[:20]}...")
        
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
            'Authorization': f'Bearer {access_token}'
        }
        logger.debug(f"Request headers: {json.dumps(headers, indent=2)}")
        
        try:
            logger.info(f"Initiating payment to URL: {url}")
            logger.info(f"Initiating payment with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"Payment request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully initiated payment: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initiating payment: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response content: {e.response.text}")
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
            "CallBackURL": current_app.config.get('MPESA_CALLBACK_URL'),
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
