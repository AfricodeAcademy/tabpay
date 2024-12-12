import hashlib
from typing import Optional
from app.main.models import UserModel



def find_user_by_hashed_msisdn(msisdn: str) -> Optional[UserModel]:
    """
    Find a user by matching their hashed phone number with a given MSISDN.
    
    Args:
        msisdn (str): The MSISDN from Safaricom Daraja API
        
    Returns:
        Optional[UserModel]: Matching user or None if not found
    """
    # Normalize MSISDN first (remove +254 prefix if exists)
    if msisdn.startswith('+254'):
        msisdn = msisdn[4:]
    elif msisdn.startswith('254'):
        msisdn = msisdn[3:]
    elif msisdn.startswith('0'):
        msisdn = msisdn[1:]
    
    # Get all users
    users = UserModel.query.all()
    
    # Hash the normalized MSISDN for comparison
    msisdn_hash = hashlib.sha256(msisdn.encode()).hexdigest()
    
    # Check each user's phone number
    for user in users:
        phone = user.phone_number
        
        # Normalize user's phone number
        if phone.startswith('+254'):
            phone = phone[4:]
        elif phone.startswith('254'):
            phone = phone[3:]
        elif phone.startswith('0'):
            phone = phone[1:]
            
        # Hash and compare
        user_phone_hash = hashlib.sha256(phone.encode()).hexdigest()
        
        if user_phone_hash == msisdn_hash:
            return user
            
    return None