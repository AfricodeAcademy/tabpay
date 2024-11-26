import os
import sys
import json
import requests
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.mpesa import MpesaCredentials, MpesaC2B, MpesaAuthManager
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv(override=True)

def test_mpesa_auth():
    """Test M-Pesa authentication"""
    print("\nTesting M-Pesa Authentication...")
    
    # Print current environment variables for debugging
    consumer_key = os.getenv('MPESA_CONSUMER_KEY')
    consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
    environment = os.getenv('MPESA_ENVIRONMENT')
    
    print(f"\nUsing credentials:")
    print(f"Consumer Key: {consumer_key}")
    print(f"Consumer Secret: {consumer_secret}")
    print(f"Environment: {environment}")
    
    credentials = MpesaCredentials(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        shortcode=os.getenv('MPESA_SHORTCODE'),
        environment=environment
    )
    
    auth_manager = MpesaAuthManager(credentials)
    print(f"Using Auth URL: {auth_manager.auth_url}")
    print(f"Using API URL: {auth_manager.api_url}")
    
    try:
        access_token = auth_manager.get_access_token()
        print("✅ Authentication successful!")
        print(f"Access Token: {access_token[:20]}...")
        return auth_manager
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_register_urls(auth_manager):
    """Test URL registration"""
    print("\nTesting URL Registration...")
    
    if not auth_manager:
        print("❌ Skipping URL registration due to authentication failure")
        return
    
    base_url = os.getenv('MPESA_CALLBACK_BASE_URL', 'https://tabpay.africa')
    confirmation_url = f"{base_url}/payments/confirmation"
    
    try:
        url = f'{auth_manager.api_url}/mpesa/c2b/v1/registerurl'
        
        payload = {
            "ShortCode": auth_manager.credentials.shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_manager.get_access_token()}'
        }
        
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print("✅ URL registration successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ URL registration failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return False

def test_payment_simulation(auth_manager):
    """Test payment simulation"""
    print("\nTesting Payment Simulation...")
    
    if not auth_manager:
        print("❌ Skipping payment simulation due to authentication failure")
        return
    
    try:
        url = f'{auth_manager.api_url}/mpesa/c2b/v1/simulate'
        
        # Test payment details
        test_phone = "254708374149"  # Test phone number
        test_amount = 100
        bill_ref = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        payload = {
            "ShortCode": auth_manager.credentials.shortcode,
            "CommandID": "CustomerPayBillOnline",
            "Amount": str(test_amount),  # Amount should be string
            "Msisdn": test_phone,
            "BillRefNumber": bill_ref
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_manager.get_access_token()}'
        }
        
        print(f"Making payment simulation request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Payment simulation successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Payment simulation failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return False

def test_mpesa_callback(test_client):
    """Test M-Pesa callback endpoint"""
    base_url = current_app.config['API_BASE_URL']

def main():
    """Main test function"""
    print("Starting M-Pesa Integration Tests...")
    
    # Test authentication
    auth_manager = test_mpesa_auth()
    if not auth_manager:
        print("\n❌ Tests failed at authentication stage")
        return
    
    # Test URL registration
    if not test_register_urls(auth_manager):
        print("\n❌ Tests failed at URL registration stage")
        return
    
    # Test payment simulation
    if not test_payment_simulation(auth_manager):
        print("\n❌ Tests failed at payment simulation stage")
        return
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main()
