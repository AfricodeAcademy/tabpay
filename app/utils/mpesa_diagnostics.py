import requests
import logging
from flask import current_app
import socket
import ssl

logger = logging.getLogger(__name__)

def test_callback_url_accessibility():
    """
    Comprehensive test for callback URL accessibility
    
    Checks:
    1. URL Reachability
    2. SSL Certificate (if HTTPS)
    3. Network Connectivity
    4. Potential Firewall Issues
    """
    try:
        callback_url = current_app.config.get('MPESA_STK_CALLBACK_URL')
        if not callback_url:
            logger.error("No callback URL configured")
            return False

        # Basic URL validation
        logger.info(f"Testing Callback URL: {callback_url}")

        # DNS Resolution Test
        try:
            parsed_url = requests.utils.urlparse(callback_url)
            socket.gethostbyname(parsed_url.netloc)
            logger.info("✅ DNS Resolution: Successful")
        except socket.gaierror:
            logger.error("❌ DNS Resolution Failed")
            return False

        # SSL Certificate Check (for HTTPS)
        if callback_url.startswith('https://'):
            try:
                hostname = parsed_url.netloc
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                        cert = secure_sock.getpeercert()
                        logger.info("✅ SSL Certificate: Valid")
            except ssl.SSLError as e:
                logger.error(f"❌ SSL Certificate Error: {e}")
                return False

        # Connectivity Test
        try:
            response = requests.post(
                callback_url, 
                json={"test": "mpesa_notification_test"},
                timeout=10
            )
            logger.info(f"✅ Connectivity Test: {response.status_code}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connectivity Test Failed: {e}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in callback URL test: {e}")
        return False

def verify_mpesa_configuration():
    """
    Verify M-Pesa related configurations
    """
    config_checks = {
        'MPESA_CONSUMER_KEY': current_app.config.get('MPESA_CONSUMER_KEY'),
        'MPESA_CONSUMER_SECRET': current_app.config.get('MPESA_CONSUMER_SECRET'),
        'MPESA_SHORTCODE': current_app.config.get('MPESA_SHORTCODE'),
        'MPESA_STK_CALLBACK_URL': current_app.config.get('MPESA_STK_CALLBACK_URL'),
        'MPESA_ENVIRONMENT': current_app.config.get('MPESA_ENVIRONMENT', 'production')
    }
    
    logger.info("🔍 M-Pesa Configuration Verification:")
    for key, value in config_checks.items():
        status = "✅ Configured" if value else "❌ Not Configured"
        logger.info(f"{key}: {status}")
    
    return all(config_checks.values())
