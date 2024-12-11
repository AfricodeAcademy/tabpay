import logging
from flask import request
from functools import wraps

logger = logging.getLogger(__name__)

# Safaricom's IP addresses for callbacks
SAFARICOM_IPS = [
    '196.201.214.200', 
    '196.201.214.206', 
    '196.201.213.114',
    '196.201.214.207', 
    '196.201.214.208', 
    '196.201.213.44', 
    '196.201.212.127', 
    '196.201.212.128', 
    '196.201.212.129', 
    '196.201.212.132', 
    '196.201.212.136', 
    '196.201.212.138', 
    '196.201.212.69', 
    '196.201.212.74',
    '10.184.20.33',
]

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

def require_safaricom_ip_validation(f):
    """Decorator to validate Safaricom IPs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_valid_safaricom_ip():
            logger.error("Request from invalid IP address")
            return {
                "ResultCode": 1,
                "ResultDesc": "Invalid request source"
            }, 403
        return f(*args, **kwargs)
    return decorated_function
