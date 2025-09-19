import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from dotenv import load_dotenv

load_dotenv()

# Create your models here.


class User(AbstractUser):
    api_key = models.CharField(
        "Chave da API",
        max_length=500,
        default='Insira uma chave de API',
        blank=True,
        help_text="Chave da api GEMINI que será utilizada pelo usuário",
    )
    system_prompt = models.CharField(
        "Prompt de sistema",
        max_length=10_000,
        default=os.getenv('SYSTEM_PROMPT','Teste'),
        blank=True,
        help_text="Prompt de sistema que determina o comportamento da IA",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name() or self.username
