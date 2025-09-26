from django.test import TestCase
from user.forms import UserUpdateForm
from user.models import User


class TestUserUpdateForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teste',
            email='teste@example.com',
            password='senha123'
        )

    def test_update_valid_user(self):
        data = {
            "email": "teste@example.com",
            "first_name": "New",
            "last_name": "User",
            "api_key": "AIza1234567890abcdefg1234567890abcdefg",
            "system_prompt": "Hello, world!"
        }
        form = UserUpdateForm(data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_update_invalid_with_email_diplicated(self):
        data = {
            "email": "teste@example.com",
            "first_name": "New",
            "last_name": "User",
            "api_key": "AIza1234567890abcdefg1234567890abcdefg",
            "system_prompt": "Hello, world!"
        }
        form = UserUpdateForm(data)
        self.assertFalse(form.is_valid())
    
    def test_update_invalid_api_key(self):
        data = {
            "email": "teste@example.com",
            "first_name": "New",
            "last_name": "User",
            "api_key": "Invalid api key",
            "system_prompt": "Hello, world!"
        }
        form = UserUpdateForm(data)
        self.assertFalse(form.is_valid())