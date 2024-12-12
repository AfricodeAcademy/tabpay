import hashlib
from typing import Optional
from app.main.models import UserModel
import logging



logger = logging.getLogger('mpesa')

def find_user_by_hashed_msisdn(hashed_msisdn: Optional[str]) -> Optional[UserModel]:
    """
    Find a user by matching their hashed phone number with Safaricom's hashed MSISDN.
    
    Args:
        hashed_msisdn (str): The pre-hashed MSISDN from Safaricom Daraja API
        
    Returns:
        Optional[UserModel]: Matching user or None if not found
    """
    if not hashed_msisdn:
        logger.warning("No hashed MSISDN provided")
        return None
        
    try:
        # Get all users
        users = UserModel.query.all()
        
        # Check each user's phone number
        for user in users:
            if not user.phone_number:
                continue
                
            phone = user.phone_number
            
            # Normalize user's phone number
            if phone.startswith('+254'):
                phone = phone[4:]
            elif phone.startswith('254'):
                phone = phone[3:]
            elif phone.startswith('0'):
                phone = phone[1:]
                
            # Hash the normalized phone number
            user_phone_hash = hashlib.sha256(phone.encode()).hexdigest()
            
            # Compare with Safaricom's hashed MSISDN
            if user_phone_hash == hashed_msisdn:
                logger.info(f"Found matching user {user.full_name} for hashed MSISDN")
                return user
                
        logger.warning(f"No matching user found for hashed MSISDN")
        return None
        
    except Exception as e:
        logger.error(f"Error matching hashed MSISDN: {str(e)}")
        return None