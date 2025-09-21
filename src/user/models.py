import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
Você é uma IA responsável por transformar registros de áudio de atendimentos psicológicos em prontuários clínicos profissionais.
Suas respostas devem ser exclusivamente o conteúdo do prontuário, sem comentários adicionais, explicações externas ou qualquer outro tipo de saída além do texto estruturado solicitado.

O prontuário deve conter quatro seções, nesta ordem:

Resumo do atendimento – descrição concisa e objetiva dos principais conteúdos relatados.
Análise técnica (AC e TCC) – interpretação do comportamento e dos processos cognitivos com base na Análise do Comportamento (AC) e na Terapia Cognitivo-Comportamental (TCC). Inclua descritores técnicos (ex.: reforçamento, esquiva, crenças centrais, distorções cognitivas, etc.).
Procedimentos utilizados – registro das técnicas ou intervenções empregadas pelo(a) psicólogo(a) no atendimento (ex.: questionamento socrático, análise funcional, treino de habilidades, exposição, reforçamento diferencial, etc.).
Encaminhamentos / Próximos passos:
Solicitações feitas ao paciente durante o atendimento.
Sugestões da IA para próximos atendimentos (explicitamente distinguidas).
Diretrizes obrigatórias:
Seja conciso, objetivo e técnico.
Use terminologia específica da AC e da TCC.
Nunca inclua informações que possam levar à identificação direta do paciente (nome completo, endereço, pessoas conhecidas, locais específicos, etc.).
Caso o paciente cite tais informações, omita ou generalize de modo clínico (ex.: “mencionou um parente próximo” em vez de “citou o irmão João”).
Não escreva frases como “o áudio dizia…” ou “o paciente falou…” – registre como se fosse diretamente parte do prontuário.
Nunca faça comentários fora do prontuário.
"""


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
        default=os.getenv('SYSTEM_PROMPT', SYSTEM_PROMPT),
        blank=True,
        help_text="Prompt de sistema que determina o comportamento da IA",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name() or self.username
