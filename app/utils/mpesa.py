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
    environment: str = 'sandbox'

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
                logger.debug(f"Using auth string: {auth_string}")
                logger.debug(f"Using auth header: Basic {auth_base64}")
                
                with requests.Session() as session:
                    response = session.get(
                        auth_url,
                        headers=headers,
                        params=params,
                        verify=True,
                        timeout=30
                    )
                
                if response.status_code != 200:
                    logger.error(f"Authentication failed with status {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    response.raise_for_status()
                
                response_data = response.json()
                logger.debug(f"Response data: {response_data}")
                
                self._access_token = response_data.get('access_token')
                if not self._access_token:
                    raise ValueError("No access token in response")
                    
                logger.info("Successfully generated access token")
                
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
            environment=current_app.config.get('MPESA_ENVIRONMENT', 'sandbox')
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
        """Register validation and confirmation URLs for C2B payments"""
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
            logger.info(f"Registering URLs with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully registered URLs: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            logger.error(f" URL registration failed: {str(e)}")
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
        else:
            # In production, we'd use STK Push instead of simulation
            url = f'{self.api_url}/mpesa/stkpush/v1/processrequest'
            
        payload = {
            "ShortCode": self.credentials.shortcode,
            "CommandID": command_id,
            "Amount": int(amount),
            "Msisdn": str(phone_number),
            "BillRefNumber": bill_ref_number
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
        }
        
        try:
            logger.info(f"Initiating payment with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully initiated payment: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initiating payment: {str(e)}")
            raise

# Create a singleton instance
mpesa_client = None

def get_mpesa_client() -> MpesaC2B:
    """Get or create the M-Pesa client singleton"""
    global mpesa_client
    if mpesa_client is None:
        mpesa_client = MpesaC2B()
    return mpesa_client
