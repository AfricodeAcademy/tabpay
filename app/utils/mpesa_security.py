import logging
from flask import request
from functools import wraps

logger = logging.getLogger(__name__)

# Safaricom's IP addresses for callbacks
SAFARICOM_IPS = [
    '196.201.214.200',
    '196.201.214.201',
    '196.201.214.202',
    '196.201.214.203',
    # Add more IPs as needed
]

def validate_mpesa_request(data):
    """Validate required fields in M-PESA callback request"""
    required_fields = {
        'validation': ['TransactionType', 'TransID', 'TransAmount', 'BusinessShortCode', 'BillRefNumber'],
        'confirmation': ['TransactionType', 'TransID', 'TransAmount', 'BusinessShortCode', 'BillRefNumber', 'TransactionTime'],
        'stk': ['MerchantRequestID', 'CheckoutRequestID', 'ResultCode', 'ResultDesc']
    }
    
    try:
        # Determine request type from path
        path = request.path.lower()
        if 'validation' in path:
            fields = required_fields['validation']
        elif 'confirmation' in path:
            fields = required_fields['confirmation']
        elif 'stk' in path:
            # For STK callbacks, data is nested
            callback_data = data.get("Body", {}).get("stkCallback", {})
            return all(field in callback_data for field in required_fields['stk'])
        else:
            logger.error(f"Unknown callback type for path: {path}")
            return False
            
        # Validate fields exist in data
        return all(field in data for field in fields)
        
    except Exception as e:
        logger.error(f"Error validating M-PESA request: {str(e)}")
        return False

def is_valid_safaricom_ip():
    """Check if request is from a valid Safaricom IP"""
    client_ip = request.remote_addr
    
    # Get X-Forwarded-For header in case behind proxy
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    is_valid = client_ip in SAFARICOM_IPS
    if not is_valid:
        logger.warning(f"Request from unauthorized IP: {client_ip}")
        
    return is_valid

def require_mpesa_validation(f):
    """Decorator to validate M-PESA requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate IP address
        if not is_valid_safaricom_ip():
            logger.error("Request from invalid IP address")
            return {
                "ResultCode": 1,
                "ResultDesc": "Invalid request source"
            }, 403
            
        # Get and validate request data
        data = request.get_json()
        if not validate_mpesa_request(data):
            logger.error("Invalid request format")
            return {
                "ResultCode": 1,
                "ResultDesc": "Invalid request format"
            }, 400
            
        return f(*args, **kwargs)
    return decorated_function
