import os
import africastalking
from typing import List
import logging

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SendSMS():
    def __init__(self):
        """Initialize Africa's Talking SMS service"""
        try:
            # Get credentials from environment variables
            username = os.getenv('AT_USERNAME')
            api_key = os.getenv('AT_API_KEY')
            self.sender_id = os.getenv('AT_SENDER_ID')
            
            if not all([username, api_key, self.sender_id]):
                raise ValueError("Missing required environment variables")
            
            
            # Initialize the SDK
            africastalking.initialize(username=username, api_key=api_key)
            self.sms = africastalking.SMS
            
            # Verify initialization by fetching account info
            try:
                account_info = africastalking.Application.fetch_application_data()
                logger.info(f"SMS service initialized successfully. Account info: {account_info}")
            except Exception as acc_error:
                logger.warning(f"Initialized but couldn't fetch account info: {acc_error}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {str(e)}")
            raise
    
    def send(self, message: str, recipients: List[str], sender_id: str = None) -> dict:
        """
        Send SMS to one or more recipients
        """
        try:
            if not message or not recipients:
                raise ValueError("Message and recipients are required")
            
            # Log the incoming data
            logger.debug(f"Sending message: '{message}'")
            logger.debug(f"Original recipients: {recipients}")
            
            # Validate phone numbers
            validated_recipients = []
            for number in recipients:
                try:
                    validated_number = self._validate_phone_number(number)
                    validated_recipients.append(validated_number)
                    logger.debug(f"Validated {number} to {validated_number}")
                except ValueError as ve:
                    logger.error(f"Validation failed for {number}: {str(ve)}")
                    raise
            
            if not validated_recipients:
                raise ValueError("No valid recipients after validation")
            
            logger.info(f"Sending message to recipients: {validated_recipients}")
            logger.debug(f"Using sender ID: {sender_id or self.sender_id}")
            
            # Send the message
            try:
                response = self.sms.send(
                    message=message,
                    recipients=validated_recipients,
                    sender_id=sender_id or self.sender_id
                )
                logger.info(f"API Response: {response}")
                
                # Verify the response
                if response and 'SMSMessageData' in response:
                    message_data = response['SMSMessageData']
                    if 'Recipients' in message_data:
                        for recipient in message_data['Recipients']:
                            logger.info(f"Delivery status for {recipient.get('number')}: {recipient.get('status')}")
                    
                return response
                
            except Exception as send_error:
                logger.error(f"Africa's Talking API error: {str(send_error)}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
    
    def _validate_phone_number(self, phone_number: str) -> str:
        """
        Validate and format phone number
        """
        try:
            logger.debug(f"Validating phone number: {phone_number}")
            
            # Remove any spaces or special characters
            cleaned_number = ''.join(filter(str.isdigit, phone_number))
            logger.debug(f"Cleaned number: {cleaned_number}")
            
            # Format the number
            if cleaned_number.startswith('254'):
                cleaned_number = '+' + cleaned_number
            elif cleaned_number.startswith('0'):
                cleaned_number = '+254' + cleaned_number[1:]
            elif not cleaned_number.startswith('+'):
                cleaned_number = '+254' + cleaned_number
            
            logger.debug(f"Formatted number: {cleaned_number}")
            
            # Basic validation
            if len(cleaned_number) < 12:  # +254 + 9 digits
                raise ValueError(f"Invalid phone number length: {phone_number}")
            
            return cleaned_number
            
        except Exception as e:
            logger.error(f"Phone number validation failed for {phone_number}: {str(e)}")
            raise ValueError(f"Invalid phone number: {phone_number}")

    def test_connection(self) -> bool:
        """
        Test the connection to Africa's Talking
        """
        try:
            account_info = africastalking.Application.fetch_application_data()
            logger.info(f"Connection test successful. Account info: {account_info}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False