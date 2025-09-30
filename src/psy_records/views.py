import json
import threading
import io

from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydantic import BaseModel

from .models import PsyRecord
from patients.models import Patient
from .forms import PsyRecordForm

from imageio_ffmpeg import get_ffmpeg_exe

AudioSegment.converter = get_ffmpeg_exe()


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
        context["patient"] = self.patient
        return context

    def form_valid(self, form):
        form.instance.patient = self.patient
        self.object = form.save(commit=False)
        self.object.content = (
            form.instance.content or "[Processando áudio em background...]"
        )
        self.object.date = form.instance.date
        self.object.save()

        # Verifica se há áudio para processar
        has_audio = self.request.POST.get("has_audio") == "true"
        audio_file = self.request.FILES.get("audio_file")

        if has_audio and audio_file:
            # audio_bytes = b"".join(chunk for chunk in audio_file.chunks())
            file_name = audio_file.name
            file_type = "mp3"
            audio_bytes = audio_file.read()

            # file_name = audio_file.name
            file_name = self.object.patient.first_name + "." + file_type

            patient_data = {
                "objectives": self.object.patient.objectives,
                "clinical_demand": self.object.patient.clinical_demand,
                "clinical_procedures": self.object.patient.clinical_procedures,
                "clinical_analysis": self.object.patient.clinical_analysis,
                "clinical_conclusion": self.object.patient.clinical_conclusion,
            }

            # Lança uma thread para processar o áudio em segundo plano
            threading.Thread(
                target=_process_audio_background,
                args=(
                    self.object.id,
                    self.object.patient.id,
                    audio_bytes,
                    file_name,
                    self.object.patient.api_key,
                    PROMPT_TRANSCRIPTION,
                    self.object.patient.system_prompt,
                    patient_data,
                ),
                daemon=True,
            ).start()

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "message": "Prontuário criado! O conteúdo será atualizado em background.",
                    "redirect_url": self.get_success_url(),
                }
            )

        messages.info(
            self.request,
            "Prontuário criado! O conteúdo do áudio será processado em background.",
        )
        # Comportamento normal (sem áudio ou em caso de erro)
        response = super().form_valid(form)

        # Se for AJAX e chegou até aqui, retorna JSON de sucesso
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "message": "Prontuário salvo com sucesso!",
                    "redirect_url": self.get_success_url(),
                }
            )

        return response

    def get_success_url(self):
        return reverse("patients:detail", args=[self.patient.id])

    def form_invalid(self, form):
        # Se for AJAX, retorna JSON com erros
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "message": "Erro nos dados do formulário",
                    "errors": form.errors,
                }
            )
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
            system_prompt_summary = user.system_prompt

            file_type = "mp3"
            audio_file = request.FILES["reprocess_audio"]
            audio_bytes = audio_file.read()

            # file_name = audio_file.name
            file_name = self.object.patient.first_name + "." + file_type

            # Atualiza o conteúdo temporariamente para indicar processamento
            self.object.content = "[Reprocessando áudio em background...]"
            self.object.save(update_fields=["content"])

            patient_data = {
                "objectives": self.object.patient.objectives,
                "clinical_demand": self.object.patient.clinical_demand,
                "clinical_procedures": self.object.patient.clinical_procedures,
                "clinical_analysis": self.object.patient.clinical_analysis,
                "clinical_conclusion": self.object.patient.clinical_conclusion,
            }

            # Lança uma thread para processar o áudio em segundo plano
            threading.Thread(
                target=_process_audio_background,
                args=(
                    self.object.id,
                    self.object.patient.id,
                    audio_bytes,
                    file_name,
                    api_key,
                    PROMPT_TRANSCRIPTION,
                    system_prompt_summary,
                    patient_data,
                ),
                daemon=True,
            ).start()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Áudio sendo reprocessado em background!",
                        "redirect_url": self.get_success_url(),
                    }
                )

            messages.info(
                request,
                "Áudio sendo reprocessado em background! O conteúdo será atualizado em breve.",
            )
            return redirect(self.get_success_url())

        # Caso não tenha reprocessamento → fluxo normal de edição de texto
        return super().post(request, *args, **kwargs)


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
        context["patient"] = self.object.patient
        return context

    def get_success_url(self):
        return reverse("patients:detail", args=[self.kwargs["patient_id"]])


# Função auxiliar


class PsySummaryData(BaseModel):
    objectives: str
    clinical_demand: str
    clinical_procedures: str
    clinical_analysis: str
    clinical_conclusion: str


class ResultPsySummaryData(PsySummaryData):
    psy_record: str


def split_audio_bytes(
    audio_bytes: io.BytesIO, mime_type: str, chunk_size_ms: int = 1_500_000
) -> list[io.BytesIO]:
    # Verificar se o arquivo é menor que 19MB
    audio_bytes.seek(0, 2)  # Move para o final do arquivo
    file_size = audio_bytes.tell()  # Obtém o tamanho em bytes
    audio_bytes.seek(0)  # Volta para o início

    # 19MB em bytes
    max_size = 19 * 1024 * 1024

    if file_size < max_size:
        return [audio_bytes]

    audio_segment = AudioSegment.from_file(audio_bytes, format=mime_type)

    chunks_data = []
    for i in range(0, len(audio_segment), chunk_size_ms):
        chunk = audio_segment[i : i + chunk_size_ms]
        chunk_io = io.BytesIO()
        chunk.export(chunk_io, format=mime_type)
        if len(chunk_io.getvalue()) % 2 != 0:
            chunk_io.seek(0)
            corrected_data = chunk_io.read()[:-1]
            if len(corrected_data) % 2 == 0:
                chunk_io = io.BytesIO(corrected_data)
                chunk_io.seek(0)
            else:
                raise ValueError(
                    "Erro de chunking persistente: O chunk ainda não é um múltiplo do tamanho do frame após a correção."
                )
        chunks_data.append(chunk_io)

    return chunks_data


def _process_audio_background(
    record_id: int,
    patient_id: int,
    audio_bytes: bytes,
    file_name: str,
    api_key: str,
    system_prompt_transcription: str,
    system_prompt_summary: str,
    patient_data: PsySummaryData,
):
    """Executa o processamento com Gemini em background"""

    audio_segment_from_upload = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio_segment_mp3 = io.BytesIO()
    audio_segment_from_upload.export(audio_segment_mp3, format="mp3")
    audio_segment_mp3.seek(0)

    # Só para depuração
    file_size_bytes = audio_segment_mp3.getbuffer().nbytes
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"Nome do arquivo recebido: {file_name}")
    print(
        f"Tamanho do arquivo em mp3: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)"
    )

    from psy_records.models import PsyRecord

    try:
        processed_content = process_audio_with_gemini(
            audio_segment_mp3,
            file_name,
            api_key,
            system_prompt_transcription,
            system_prompt_summary,
            patient_data,
        )
        patient = Patient.objects.get(id=patient_id)
        record = PsyRecord.objects.get(id=record_id)
        if processed_content:
            patient.objectives = processed_content.get("objectives")
            patient.clinical_demand = processed_content.get("clinical_demand")
            patient.clinical_procedures = processed_content.get("clinical_procedures")
            patient.clinical_analysis = processed_content.get("clinical_analysis")
            patient.clinical_conclusion = processed_content.get("clinical_conclusion")

            record.content = processed_content.get("psy_record")
        else:
            record.content = "⚠ Não foi possível processar o áudio."
        patient.save(
            update_fields=[
                "objectives",
                "clinical_demand",
                "clinical_procedures",
                "clinical_analysis",
                "clinical_conclusion",
            ]
        )
        record.save(update_fields=["content"])
    except Exception as e:
        record = PsyRecord.objects.get(id=record_id)
        record.content = f"⚠ Erro ao processar áudio: {e}"
        record.save(update_fields=["content"])


def process_audio_with_gemini(
    audio_bytes: io.BytesIO,
    file_name: str,
    api_key: str,
    system_prompt_transcription: str,
    system_prompt_summary: str,
    patient_data: PsySummaryData,
) -> ResultPsySummaryData:
    """
    Processa o arquivo de áudio usando Google Gemini com upload inline
    """
    try:
        # Verifica se o usuário tem API key configurada
        if not api_key:
            raise ValueError("API key do Gemini não configurada para este usuário")

        # Configura o Gemini com a API key do usuário
        client = genai.Client(api_key=api_key)

        file_type = get_audio_type(file_name)
        mime_type = get_audio_mime_type(file_name)

        # Gera o conteúdo usando upload inline
        splited_audio_bytes = split_audio_bytes(audio_bytes, file_type)

        data = []
        for i, chunk in enumerate(splited_audio_bytes):
            data.append(
                types.Part.from_bytes(data=chunk.getvalue(), mime_type=mime_type)
            )

        print(f"### processando {file_name} ###")
        transcription_response = client.models.generate_content(
            model="gemini-2.5-flash", contents=[system_prompt_transcription, data]
        )

        import re

        patient_data_json = json.dumps(patient_data, ensure_ascii=False)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                system_prompt_summary,
                patient_data_json,
                transcription_response.text,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": ResultPsySummaryData,
            }
        )

        update_text = response.text
        json_match = re.search(r"\{.*\}", update_text, re.DOTALL)
        if json_match:
            processed_content = json.loads(json_match.group())
        else:
            processed_content = {"psy_record": update_text}

        print("### Processamento concluído ###")
        return processed_content

    except Exception as e:
        print(f"Erro ao processar áudio com Gemini: {str(e)}")
        return None


def get_audio_type(file_name: str) -> str:
    """
    Determina a extensão do arquivo
    """
    extension = file_name.split(".")[-1].lower()
    return extension


def get_audio_mime_type(file_name: str) -> str:
    """
    Determina o MIME type baseado na extensão do arquivo
    """
    extension = file_name.split(".")[-1].lower()

    mime_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mp3",
        ".aiff": "audio/aiff",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",  # Para gravações do navegador
    }
    return mime_types["." + extension]


PROMPT_TRANSCRIPTION = """
Você é um transcritor clínico. Sua tarefa é transcrever a gravação da sessão verbalizando trocas entre participantes.

Regras obrigatórias:
1) Responda EXCLUSIVAMENTE com um único OBJETO JSON válido (UTF-8) e nada mais.
2) O objeto JSON deve conter a chave "transcription" (string). Não inclua outras chaves.
3) A transcrição deve diferenciar falantes usando rótulos padronizados em português: "Psicólogo:", "Paciente:", "Familiar:", "Outro:" (use apenas os rótulos relevantes).
4) Separe cada fala em nova linha com o rótulo do falante no início da linha. Exemplo: "Paciente: ...\nPsicólogo: ...".
5) Preserve o conteúdo verbal (transcreva literalmente quando possível). Para trechos inaudíveis, insira o marcador "[inaudível]".
6) NÃO inclua timestamps, metadados ou comentários. NÃO generalize nomes automaticamente — se houver identificação direta, substitua por "[parente]" ou "[local]" e anote nada mais além da transcrição.
7) Não tente resumir, interpretar ou corrigir o texto; faça transcrição fiel.
8) Se não der para identificar o falante em um trecho, use "Outro:".
Fim.
"""
