from django.test import TestCase
from user.models import User


class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teste',
            email='teste@example.com',
            password='senha123'
        )

    def test_user_creation(self):
        self.assertTrue(User.objects.filter(username='teste').exists())
    
    def test_user_authentication(self):
        user = User.objects.get(username='teste')
        self.assertTrue(user.check_password('senha123'))
    
    def test_api_key(self):
        user = User.objects.get(username='teste')
        self.assertIsNotNone(user.api_key)
    
    def test_user_str(self):
        user = User.objects.get(username='teste')
        self.assertTrue(str(user), 'teste')