import os
import sys
import unittest
import json
from datetime import datetime, timezone

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.main.models import (
    PaymentModel, UserModel, BankModel, BlockModel, 
    MeetingModel, UmbrellaModel, ZoneModel, RoleModel
)

class TestMpesaAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
    def setUp(self):
        self.client = self.app.test_client()
        db.create_all()
        self.create_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def create_test_data(self):
        # Create test user first (for created_by references)
        user = UserModel(
            email=f"test_{datetime.now(timezone.utc).timestamp()}@example.com",  
            full_name="Test User",
            phone_number="254712345678",
            is_approved=True
        )
        db.session.add(user)
        db.session.flush()  # Get user.id
        
        # Create test umbrella with required fields
        umbrella = UmbrellaModel(
            name="Test Umbrella",
            location="Test Location",  
            created_by=user.id,  
            initials="TU"
        )
        db.session.add(umbrella)
        db.session.flush()
        
        # Create test block
        block = BlockModel(
            name="Test Block",
            parent_umbrella_id=umbrella.id,
            created_by=user.id,
            initials="TB"  
        )
        db.session.add(block)
        db.session.flush()
        
        # Create test zone
        zone = ZoneModel(
            name="Test Zone",
            parent_block_id=block.id,  
            created_by=user.id
        )
        db.session.add(zone)
        db.session.flush()
        
        # Create test bank
        bank = BankModel(
            name="Test Bank",
            paybill_no="123456"
        )
        db.session.add(bank)
        db.session.flush()
        
        # Update user with bank and umbrella
        user.bank_id = bank.id
        user.umbrella_id = umbrella.id
        
        # Create test meeting
        meeting = MeetingModel(
            date=datetime.now(timezone.utc),
            host_id=user.id,
            block_id=block.id,
            zone_id=zone.id,
            organizer_id=user.id,
            unique_id="MEET001"  
        )
        db.session.add(meeting)
        
        # Commit all test data
        db.session.commit()
        
        # Store IDs for use in tests
        self.test_bank_id = bank.id
        self.test_block_id = block.id
        self.test_user_id = user.id
        self.test_meeting_id = meeting.id

    def test_create_mpesa_payment(self):
        """Test creating a new M-Pesa payment"""
        payment_data = {
            "mpesa_id": "TEST123456789",
            "account_number": "ACC123",
            "source_phone_number": "254712345678",
            "amount": 1000,
            "payment_date": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "transaction_status": True,
            "bank_id": self.test_bank_id,
            "block_id": self.test_block_id,
            "payer_id": self.test_user_id,
            "meeting_id": self.test_meeting_id,
            "transaction_type": "CustomerPayBillOnline",
            "business_short_code": "174379",
            "invoice_number": "INV001",
            "org_account_balance": 5000.0,
            "third_party_trans_id": "3rd123",
            "first_name": "John",
            "middle_name": "Doe",
            "last_name": "Smith"
        }

        response = self.client.post(
            '/api/v1/payments/',
            data=json.dumps(payment_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['mpesa_id'], "TEST123456789")
        self.assertEqual(data['amount'], 1000)
        self.assertEqual(data['transaction_type'], "CustomerPayBillOnline")

    def test_get_payment(self):
        """Test retrieving a payment"""
        # First create a payment
        payment = PaymentModel(
            mpesa_id="TEST987654321",
            account_number="ACC456",
            source_phone_number="254712345678",
            amount=2000,
            bank_id=self.test_bank_id,
            block_id=self.test_block_id,
            payer_id=self.test_user_id,
            meeting_id=self.test_meeting_id,
            transaction_type="CustomerPayBillOnline",
            business_short_code="174379",
            first_name="Jane",
            last_name="Doe"
        )
        db.session.add(payment)
        db.session.commit()

        # Get the payment
        response = self.client.get(f'/api/v1/payments/{payment.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['mpesa_id'], "TEST987654321")
        self.assertEqual(data['amount'], 2000)

    def test_update_payment(self):
        """Test updating a payment"""
        # First create a payment
        payment = PaymentModel(
            mpesa_id="TEST555555555",
            account_number="ACC789",
            source_phone_number="254712345678",
            amount=3000,
            bank_id=self.test_bank_id,
            block_id=self.test_block_id,
            payer_id=self.test_user_id,
            meeting_id=self.test_meeting_id
        )
        db.session.add(payment)
        db.session.commit()

        # Update the payment
        update_data = {
            "transaction_status": True,
            "org_account_balance": 8000.0
        }

        response = self.client.patch(
            f'/api/v1/payments/{payment.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['transaction_status'], True)
        self.assertEqual(data['org_account_balance'], 8000.0)

    def test_filter_payments(self):
        """Test filtering payments"""
        # Create two payments
        payment1 = PaymentModel(
            mpesa_id="FILTER_TEST_1",
            account_number="ACC001",
            source_phone_number="254712345678",
            amount=1000,
            bank_id=self.test_bank_id,
            block_id=self.test_block_id,
            payer_id=self.test_user_id,
            meeting_id=self.test_meeting_id
        )
        payment2 = PaymentModel(
            mpesa_id="FILTER_TEST_2",
            account_number="ACC002",
            source_phone_number="254712345678",
            amount=2000,
            bank_id=self.test_bank_id,
            block_id=self.test_block_id,
            payer_id=self.test_user_id,
            meeting_id=self.test_meeting_id
        )
        db.session.add(payment1)
        db.session.add(payment2)
        db.session.commit()

        # Test filtering by meeting_id
        response = self.client.get(f'/api/v1/payments/?meeting_id={self.test_meeting_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

        # Test filtering by mpesa_id
        response = self.client.get('/api/v1/payments/?mpesa_id=FILTER_TEST_1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['mpesa_id'], "FILTER_TEST_1")

if __name__ == '__main__':
    unittest.main()
