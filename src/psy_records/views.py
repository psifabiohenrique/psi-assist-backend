import threading

from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
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
        self.object = form.save(commit=False)
        self.object.content = form.instance.content or "[Processando áudio em background...]"
        self.object.date = form.instance.date
        self.object.save()
        
        # Verifica se há áudio para processar
        has_audio = self.request.POST.get('has_audio') == 'true'
        audio_file = self.request.FILES.get('audio_file')
        
        if has_audio and audio_file:
            audio_bytes = b"".join(chunk for chunk in audio_file.chunks())
            file_name = audio_file.name
            # Lança uma thread para processar o áudio em segundo plano
            threading.Thread(
                target=self._process_audio_background,
                args=(self.object.id, audio_bytes, file_name, self.request.user.api_key, self.request.user.system_prompt),
                daemon=True
            ).start()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Prontuário criado! O conteúdo será atualizado em background.',
                'redirect_url': self.get_success_url()
            })

        messages.info(
            self.request,
            "Prontuário criado! O conteúdo do áudio será processado em background."
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

    def process_audio_with_gemini(self, audio_bytes, file_name, api_key, system_prompt):
        """
        Processa o arquivo de áudio usando Google Gemini com upload inline
        """
        try:
            # Verifica se o usuário tem API key configurada
            if not api_key:
                raise ValueError("API key do Gemini não configurada para este usuário")
            
            # Configura o Gemini com a API key do usuário
            client = genai.Client(api_key=api_key)
            
            # Determina o MIME type baseado na extensão do arquivo
            mime_type = get_audio_mime_type(file_name)
            
            # Prepara o prompt do sistema
            system_prompt = system_prompt or "Você é um assistente especializado em análise de sessões de psicoterapia."
            
            # Gera o conteúdo usando upload inline
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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
                    max_output_tokens=5000
                )
            )
            
            # Retorna o texto gerado
            return response.text if response.text else None
            
        except Exception as e:
            print(f"Erro ao processar áudio com Gemini: {str(e)}")
            return None

    def _process_audio_background(self, record_id, audio_bytes, file_name, api_key, system_prompt):
        """Executa o processamento com Gemini em background"""
        from psy_records.models import PsyRecord

        try:
            processed_content = self.process_audio_with_gemini(audio_bytes, file_name, api_key, system_prompt)
            record = PsyRecord.objects.get(id=record_id)
            if processed_content:
                record.content = processed_content
            else:
                record.content = "⚠ Não foi possível processar o áudio."
            record.save(update_fields=['content'])
        except Exception as e:
            record = PsyRecord.objects.get(id=record_id)
            record.content = f"⚠ Erro ao processar áudio: {e}"
            record.save(update_fields=['content'])

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
            patient__user=self.request.user,
            patient_id=self.kwargs["patient_id"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Caso o usuário tenha enviado áudio para reprocessar
        if "reprocess_audio" in request.FILES:
            user = request.user
            api_key = user.api_key
            system_prompt = user.system_prompt

            audio_file = request.FILES["reprocess_audio"]
            audio_bytes = audio_file.read()
            file_name = audio_file.name

            # Atualiza o conteúdo temporariamente para indicar processamento
            self.object.content = "[Reprocessando áudio em background...]"
            self.object.save(update_fields=['content'])

            # Lança uma thread para processar o áudio em segundo plano
            threading.Thread(
                target=self._process_audio_background,
                args=(self.object.id, audio_bytes, file_name, api_key, system_prompt),
                daemon=True
            ).start()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    'success': True,
                    'message': 'Áudio sendo reprocessado em background!',
                    'redirect_url': self.get_success_url()
                })

            messages.info(
                request,
                "Áudio sendo reprocessado em background! O conteúdo será atualizado em breve."
            )
            return redirect(self.get_success_url())

        # Caso não tenha reprocessamento → fluxo normal de edição de texto
        return super().post(request, *args, **kwargs)

    def _process_audio_background(self, record_id, audio_bytes, file_name, api_key, system_prompt):
        """Executa o reprocessamento com Gemini em background"""
        from psy_records.models import PsyRecord

        try:
            processed_content = self.process_audio_with_gemini(audio_bytes, file_name, api_key, system_prompt)
            record = PsyRecord.objects.get(id=record_id)
            if processed_content:
                record.content = processed_content
            else:
                record.content = "⚠ Não foi possível reprocessar o áudio."
            record.save(update_fields=['content'])
        except Exception as e:
            record = PsyRecord.objects.get(id=record_id)
            record.content = f"⚠ Erro ao reprocessar áudio: {e}"
            record.save(update_fields=['content'])

    def process_audio_with_gemini(self, audio_bytes, file_name, api_key, system_prompt):
        """
        Processa o arquivo de áudio usando Google Gemini com upload inline
        """
        try:
            # Verifica se o usuário tem API key configurada
            if not api_key:
                raise ValueError("API key do Gemini não configurada para este usuário")

            # Configura o Gemini com a API key do usuário
            client = genai.Client(api_key=api_key)

            # Determina o MIME type baseado na extensão do arquivo
            mime_type = get_audio_mime_type(file_name)

            # Prepara o prompt do sistema
            system_prompt = system_prompt or "Você é um assistente especializado em análise de sessões de psicoterapia."

            # Gera o conteúdo usando upload inline
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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
                    max_output_tokens=5000
                )
            )

            # Retorna o texto gerado
            return response.text if response.text else None

        except Exception as e:
            print(f"Erro ao processar áudio com Gemini: {str(e)}")
            return None


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


# Função auxiliar

def get_audio_mime_type(file_name):
        """
        Determina o MIME type baseado na extensão do arquivo
        """
        extension = file_name[1].lower()
        
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