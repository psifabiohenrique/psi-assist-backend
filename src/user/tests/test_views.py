from django.test import TestCase
from http import HTTPStatus
from django.urls import reverse
from user.models import User


class TestViews(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.signup_url = reverse('user:signup')

    def test_signup_view_get(self):
        response = self.client.get(self.signup_url)
        
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'user/signup.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Cadastrar - Psi Assist')
    
    def test_signup_pass(self):
        data = {
            "username": 'teste',
            "email": 'teste@teste.com',
            "first_name": 'teste',
            "last_name": 'teste',
            "api_key": 'AIza1234567890abcdefg1234567890abcdefg',
            "system_prompt": 'teste',
            'password1': 'senhaSegura123!',
            'password2': 'senhaSegura123!',
        }
        response = self.client.post(self.signup_url, data=data)

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual(user.username, 'teste')
            self.assertTrue(user.is_authenticated)
        self.assertRedirects(response, reverse('patients:list'))
    
    def test_signup_fail(self):
        data = {
            "username": 'teste',
            "email": 'teste@teste.com',
            "first_name": 'teste',
            "last_name": 'teste',
            "api_key": 'AIza1234567890abcdefg1234567890abcdefg',
            "system_prompt": 'teste',
            'password1': 'senhaSegura123!',
            'password2': 'outraSenhaSegura123!',
        }
        response = self.client.post(self.signup_url, data=data)

        self.assertEqual(User.objects.count(), 0)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/signup.html')

        form = response.context.get('form')
        self.assertIsNotNone(form)
        if form:
            self.assertIsNotNone(form, "A view não colocou 'form' no contexto.")
            self.assertTrue(form.errors, "Esperava erros de validação no formulário.")
            self.assertFormError(form, 'password2', 'Os dois campos de senha não correspondem.') # type: ignore
