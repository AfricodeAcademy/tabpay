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
        logger.debug(f"Found {len(users)} users to check")
        
        # Check each user's phone number
        for user in users:
            if not user.phone_number:
                continue
                
            phone = user.phone_number
            original_phone = phone
            
            # Try different phone number formats
            formats_to_try = [
                phone,  # Original format
                phone.lstrip('+'),  # Remove leading +
                phone.lstrip('0'),  # Remove leading 0
                '254' + phone.lstrip('+254').lstrip('0')  # Ensure 254 prefix
            ]
            
            for phone_format in formats_to_try:
                # Hash the phone number
                user_phone_hash = hashlib.sha256(phone_format.encode()).hexdigest()
                logger.debug(f"Testing format: {phone_format} -> hash: {user_phone_hash}")
                
                # Compare with Safaricom's hashed MSISDN
                if user_phone_hash == hashed_msisdn:
                    logger.info(f"Found matching user {user.full_name} for hashed MSISDN. Format used: {phone_format}")
                    return user
                    
        logger.warning(f"No matching user found for hashed MSISDN after trying all formats")
        return None
        
    except Exception as e:
        logger.error(f"Error matching hashed MSISDN: {str(e)}")
        return None