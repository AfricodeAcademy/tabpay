# FILE: network_diagnostics.py
import socket
import requests
import logging
import ssl
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from urllib3.exceptions import InsecureRequestWarning
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

class NetworkDiagnostics:
    def __init__(self):
        self.session = self._create_session()
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _create_session(self):
        session = requests.Session()
        # Suppress only the specific InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[400, 401, 403, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]  # Updated parameter
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.verify = True  # Enable SSL verification
        return session

    def check_network_configuration(self):
        """
        Comprehensive network configuration diagnostic for M-Pesa callback URLs
        """
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # M-Pesa Callback URLs from .env
        callback_urls = [
            os.getenv('MPESA_STK_CALLBACK_URL'),
            os.getenv('MPESA_VALIDATION_URL'),
            os.getenv('MPESA_CONFIRMATION_URL'),
            os.getenv('MPESA_CALLBACK_URL'),
            os.getenv('MPESA_CALLBACK_BASE_URL')
        ]

        # Remove None values and duplicates
        callback_urls = list(set(filter(None, callback_urls)))

        logger.info("🔍 Checking Network Configuration for M-Pesa Callback URLs")
        
        results = {}
        for url in callback_urls:
            try:
                # Parse the URL
                parsed_url = urlparse(url)
                hostname = parsed_url.netloc
                
                logger.info(f"\n🌐 Checking URL: {url}")

                # DNS Resolution
                try:
                    ip_address = socket.gethostbyname(hostname)
                    logger.info(f"✅ DNS Resolution: {hostname} resolves to {ip_address}")
                    results[url] = {"dns": True}
                except socket.gaierror:
                    logger.error("❌ DNS Resolution Failed")
                    results[url] = {"dns": False}
                    continue  # Skip further checks if DNS fails

                # Check Open Ports
                open_ports = []
                for port in [80, 443, 8080]:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(5)
                        result = sock.connect_ex((hostname, port))
                        if result == 0:
                            open_ports.append(port)
                            logger.info(f"✅ Port {port} is open")
                        else:
                            logger.warning(f"⚠️ Port {port} is closed")
                results[url]["open_ports"] = open_ports

                # SSL Certificate Verification
                try:
                    context = ssl.create_default_context()
                    with context.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                        s.connect((hostname, 443))
                        cert = s.getpeercert()
                    logger.info("✅ SSL Certificate: Valid")
                    results[url]["ssl"] = True
                except ssl.SSLError:
                    logger.error("❌ SSL Certificate: Invalid")
                    results[url]["ssl"] = False

                # Test Callback Endpoint
                response = self.test_callback_endpoint(url)
                if response:
                    logger.info(f"Callback Test: HTTP Status {response.status_code}")
                    logger.info(f"Response Headers: {dict(response.headers)}")
                    logger.info(f"Response Content: {response.text}")
                else:
                    logger.error("❌ Callback Test Failed")
                
            except Exception as e:
                logger.error(f"❌ Error checking {url}: {str(e)}")

        # Summary
        logger.info("\n🔬 M-Pesa Callback URL Network Diagnostic Summary:")
        for url, result in results.items():
            logger.info(f"\nURL: {url}")
            logger.info(f"DNS Resolution: {'✅ Passed' if result.get('dns') else '❌ Failed'}")
            logger.info(f"Open Ports: {result.get('open_ports', [])}")
            logger.info(f"SSL Certificate: {'✅ Valid' if result.get('ssl') else '❌ Invalid'}")

    def test_callback_endpoint(self, url):
        headers = self.headers.copy()
        
        # Sample M-Pesa callback payload
        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "test-123",
                    "CheckoutRequestID": "ws_CO_123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1.00},
                            {"Name": "MpesaReceiptNumber", "Value": "TEST123456"},
                            {"Name": "TransactionDate", "Value": 20240101000000},
                            {"Name": "PhoneNumber", "Value": 254700000000}
                        ]
                    }
                }
            }
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

if __name__ == "__main__":
    diagnostics = NetworkDiagnostics()
    diagnostics.check_network_configuration()