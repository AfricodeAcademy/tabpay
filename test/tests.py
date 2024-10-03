import unittest
from app import create_app
from app.utils import db
from app.main.models import UserModel

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_users(self):
        response = self.client.get('/api/v1/users')
        self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        user_data = {
            'email': 'test@example.com',
            'password': 'password123',
            'id_number': '123456789',
            'full_name': 'Test User'
        }
        response = self.client.post('/api/v1/users', json=user_data)
        self.assertEqual(response.status_code, 201)

    # Add more test methods for other endpoints and HTTP methods

if __name__ == '__main__':
    unittest.main()