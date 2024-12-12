from flask_sqlalchemy import SQLAlchemy
from flask_mailman import Mail
import secrets
from PIL import Image
from flask import current_app
import logging
import os
from flask_wtf.csrf import CSRFProtect
import hashlib
from typing import Optional
from app.main.models import UserModel
# from .send_sms import SendSMS # SMS service
# import africastalking


db = SQLAlchemy()
mail = Mail()
csrf = CSRFProtect()

# SMS service
# Initialize SMS service as None first
# sms = None

# def init_sms(app):
#     """Initialize SMS service with application config"""
#     global sms
#     try:
#         sms = SendSMS()
#         return sms
#     except Exception as e:
#         app.logger.error(f"Failed to initialize SMS service: {e}")
#         return None
    # SMS service - ENDS********

# Function to save the profile picture
def save_picture(form_picture):
    try:
        # Generate a random hex for the filename and get the file extension
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext

        # Ensure the directory exists and log the action
        image_dir = os.path.join(current_app.root_path, 'static/images')
        if not os.path.exists(image_dir):
            logging.info(f"Directory {image_dir} does not exist. Creating directory...")
            os.makedirs(image_dir)
        else:
            logging.info(f"Directory {image_dir} already exists.")

        # Create the path to save the image
        picture_path = os.path.join(image_dir, picture_fn)

        # Resize the image and save it
        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        logging.info(f"Profile picture saved at {picture_path}")
        return picture_fn

    except Exception as e:
        logging.error(f"Error saving picture: {e}")
        raise e
    
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


__all__ = ['db', 'mail'] # SMS service
