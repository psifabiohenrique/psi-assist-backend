import os
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from google import genai
from google.genai import types

from .models import PsyRecord
from patients.models import Patient
from .forms import PsyRecordForm


class PsyRecordCreateView(LoginRequiredMixin, CreateView):
    model = PsyRecord
    form_class = PsyRecordForm
    template_name = "psy_records/psyrecord_form.html"
    context_object_name = "record"

    def dispatch(self, request, *args, **kwargs):
        self.patient = get_object_or_404(
            Patient, id=kwargs["patient_id"], user=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.patient
        return context

    def form_valid(self, form):
        form.instance.patient = self.patient
        
        # Verifica se há áudio para processar
        has_audio = self.request.POST.get('has_audio') == 'true'
        audio_file = self.request.FILES.get('audio_file')
        
        if has_audio and audio_file:
            # Processa o áudio com Gemini
            try:
                processed_content = self.process_audio_with_gemini(audio_file)
                if processed_content:
                    form.instance.content = processed_content
                    
                    # Se for uma requisição AJAX, retorna JSON
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        # Salva o prontuário
                        self.object = form.save()
                        return JsonResponse({
                            'success': True,
                            'message': 'Prontuário processado e salvo com sucesso!',
                            'redirect_url': self.get_success_url()
                        })
                else:
                    # Se falhou o processamento, mantém o conteúdo original do form
                    messages.warning(
                        self.request, 
                        'Não foi possível processar o áudio. O prontuário foi salvo com o conteúdo digitado.'
                    )
            except Exception as e:
                # Em caso de erro, mantém o conteúdo original
                messages.error(
                    self.request,
                    f'Erro ao processar áudio: {str(e)}. O prontuário foi salvo com o conteúdo digitado.'
                )
        
        # Comportamento normal (sem áudio ou em caso de erro)
        response = super().form_valid(form)
        
        # Se for AJAX e chegou até aqui, retorna JSON de sucesso
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Prontuário salvo com sucesso!',
                'redirect_url': self.get_success_url()
            })
            
        return response

    def process_audio_with_gemini(self, audio_file):
        """
        Processa o arquivo de áudio usando Google Gemini com upload inline
        """
        try:
            # Verifica se o usuário tem API key configurada
            if not self.request.user.api_key:
                raise ValueError("API key do Gemini não configurada para este usuário")
            
            # Configura o Gemini com a API key do usuário
            client = genai.Client(api_key=self.request.user.api_key)
            
            # Lê os bytes do áudio diretamente do arquivo Django
            audio_bytes = b''
            for chunk in audio_file.chunks():
                audio_bytes += chunk
            
            # Determina o MIME type baseado na extensão do arquivo
            mime_type = self.get_audio_mime_type(audio_file)
            
            # Prepara o prompt do sistema
            system_prompt = self.request.user.system_prompt or "Você é um assistente especializado em análise de sessões de psicoterapia."
            
            # Gera o conteúdo usando upload inline
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    "Por favor, analise este áudio de sessão de psicoterapia e gere um registro de prontuário profissional seguindo as diretrizes do system prompt.",
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # Retorna o texto gerado
            return response.text if response.text else None
            
        except Exception as e:
            print(f"Erro ao processar áudio com Gemini: {str(e)}")
            return None

    def get_audio_mime_type(self, audio_file):
        """
        Determina o MIME type baseado na extensão do arquivo
        """
        extension = os.path.splitext(audio_file.name)[1].lower()
        
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mp3', 
            '.aiff': 'audio/aiff',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.webm': 'audio/webm'  # Para gravações do navegador
        }
        
        return mime_types.get(extension, 'audio/wav')

    def get_success_url(self):
        return reverse("patients:detail", args=[self.patient.id])

    def form_invalid(self, form):
        # Se for AJAX, retorna JSON com erros
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Erro nos dados do formulário',
                'errors': form.errors
            })
        return super().form_invalid(form)


class PsyRecordDetailView(LoginRequiredMixin, DetailView):
    model = PsyRecord
    template_name = "psy_records/psyrecord_detail.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )


class PsyRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = PsyRecord
    form_class = PsyRecordForm
    template_name = "psy_records/psyrecord_form.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])


class PsyRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = PsyRecord
    template_name = "psy_records/psyrecord_confirm_delete.html"
    context_object_name = "record"

    def get_queryset(self):
        return PsyRecord.objects.filter(
            patient__user=self.request.user, patient_id=self.kwargs["patient_id"]
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])
