import io
import json
import os
import subprocess
import tempfile
import threading
import logging

from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from google import genai
from google.genai import types, errors
from pydantic import BaseModel
from dotenv import load_dotenv

from .models import PsyRecord
from patients.models import Patient
from .forms import PsyRecordForm

load_dotenv()
logger = logging.getLogger(__name__)

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

        logger.info(f'Começando o processamento via post: {self.patient.full_name}')

        # Verifica se há áudio para processar
        has_audio = self.request.POST.get("has_audio") == "true"
        audio_file = self.request.FILES.get("audio_file")

        if has_audio and audio_file:
            logger.info('Criando temp_file')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
            try:
                logger.info('Iniciando o loop nos chunks')
                # loop = 0
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                    # logger.info(f'{loop} ')
                    # loop += 1
                temp_file.close()

                logger.info("Arquivo temporário finalizado")
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Não foi possível processar o arquivo, tente novamente!",
                        "redirect_url": self.get_success_url(),
                    }
                )
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
                    temp_file,
                    self.request.user.api_key,
                    PROMPT_TRANSCRIPTION,
                    self.request.user.system_prompt,
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

            else: # Não é AJAX, mas tem áudio
                messages.info(
                    self.request,
                    "Prontuário criado! O conteúdo do áudio será processado em background.",
                )
                return redirect(self.get_success_url())
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

        logger.info('Começando o processamento via post')

        # Caso o usuário tenha enviado áudio para reprocessar
        if "reprocess_audio" in request.FILES:

            user = request.user
            api_key = user.api_key
            system_prompt_summary = user.system_prompt


            audio_file = request.FILES["reprocess_audio"]

            logger.info('Criando temp_file')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
            try:
                logger.info(audio_file.temporary_file_path())
                logger.info('Iniciando o loop nos chunks')
                loop = 0
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                    # print(f'{loop} ', end='')
                    loop += 1
                temp_file.close()

                logger.info("Arquivo temporário finalizado")
            except Exception:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Não foi possível processar o arquivo, tente novamente!",
                        "redirect_url": self.get_success_url(),
                    }
                )
            
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
                    temp_file,
                    api_key,
                    PROMPT_TRANSCRIPTION,
                    system_prompt_summary,
                    patient_data,
                ),
                daemon=True,
            ).start()

            # Atualiza o conteúdo temporariamente para indicar processamento
            self.object.content = "[Reprocessando áudio em background...]"
            self.object.save(update_fields=["content"])

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Áudio sendo reprocessado em background!",
                        "redirect_url": self.get_success_url(),
                    }
                )

            else: # Não é AJAX, mas tem áudio
                messages.info(
                    self.request,
                    "Áudio sendo reprocessado em background! O conteúdo será atualizado em breve.""Prontuário criado! O conteúdo do áudio será processado em background.",
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


def _process_audio_background(
    record_id: int,
    patient_id: int,
    audio_file: tempfile._TemporaryFileWrapper,
    api_key: str,
    system_prompt_transcription: str,
    system_prompt_summary: str,
    patient_data: PsySummaryData,
):
    """Executa o processamento com Gemini em background"""

    logger.info(f"Iniciando processamento de áudio para record_id: {record_id} - {patient_id}")
    try:

        from psy_records.models import PsyRecord

        try:
            
            logger.info('Iniciando a função process_audio_with_gemini')
            processed_content = process_audio_with_gemini(
                audio_file,
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
    
    finally:
        try:
            if os.path.exists(audio_file):
                os.unlink(audio_file)
                print(f"Arquivo temporário {audio_file} removido.")
        except Exception:
            print(f"Falha ao apagar arquivo temporário {audio_file}.")


def process_audio_with_gemini(
    audio_file: tempfile._TemporaryFileWrapper,
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

        audio_bytes = split_audio_with_ffmpeg_into_chunks(audio_file.name)

        part_list = []

        for i in audio_bytes:
            part_list.append(types.Part.from_bytes(data=i.getvalue(), mime_type="audio/webm"))
            i.close()
        del audio_bytes[:]

        logger.info("Enviando requisição de transcrição para o gemini")
        try:
            transcription_response = client.models.generate_content(
                model=os.getenv('GEMINI_MODEL', "gemini-2.5-flash"), contents=[system_prompt_transcription, part_list]
            )
        except errors.APIError as e:
            return {"psy_record": f"Erro na transcrição do áudio, código: {e.code}. \n\n {e.message}"}

        del part_list

        import re

        logger.info("Transcrição concluida")
        patient_data_json = json.dumps(patient_data, ensure_ascii=False)
        logger.info("Iniciando a produção do prontuário")

        try:
            response = client.models.generate_content(
                model=os.getenv('GEMINI_MODEL', "gemini-2.5-flash"),
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
        except errors.APIError as e:
            return {"psy_record": f"Erro no processamento do prontuário, código: {e.code}. \n\n {e.message}"}

        logger.info("Prontuário escrito")
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
        result = {
            'objectives': '',
            'clinical_demand': '',
            'clinical_procedures': '',
            'clinical_analysis': '',
            'clinical_conclusion': '',
            'psy_record': str(e)
        }
        return None


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

def split_audio_with_ffmpeg_into_chunks(input_filepath: str, max_chunk_size_mb: int = 19) -> list[io.BytesIO] | None:
    """
    Divide um arquivo de áudio grande em múltiplos arquivos menores (chunks) usando FFmpeg,
    limitando o tamanho de cada chunk. Os chunks são retornados como uma lista de io.BytesIO.

    Args:
        input_filepath: Caminho completo para o arquivo de áudio de entrada.
        max_chunk_size_mb: Tamanho máximo desejado para cada chunk em megabytes.

    Returns:
        Uma lista de objetos io.BytesIO, cada um contendo um chunk de áudio,
        ou None em caso de falha.
    """
    chunk_buffers = []
    temp_dir = None # Para gerenciar arquivos temporários de saída do ffmpeg

    try:
        # 1. Obter informações do arquivo de entrada para estimar a duração por MB
        # Usamos ffprobe para isso
        ffprobe_command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,size',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_filepath
        ]
        
        logger.debug(f"Executando ffprobe: {' '.join(ffprobe_command)}")
        ffprobe_result = subprocess.run(ffprobe_command, check=True, capture_output=True, text=True)
        duration_str, size_bytes_str = ffprobe_result.stdout.strip().split('\n')
        print(f"Duration_str: {duration_str}, size_bytes: {size_bytes_str}")
        total_size_bytes = int(size_bytes_str)
        
        if total_size_bytes == 0:
            logger.error(f"Arquivo de entrada {input_filepath} tem tamanho 0.")
            return None

             
        # 2. Criar um diretório temporário para os arquivos de saída do FFmpeg
        # O ffmpeg pode criar vários arquivos de saída, então um diretório é melhor
        temp_dir = tempfile.mkdtemp()
        output_filename_pattern = os.path.join(temp_dir, "chunk_%03d.webm") # Saída sempre em webm para consistência
        
        # 3. Comando FFmpeg para dividir o áudio
        # Usamos `-segment_time` para dividir por tempo. Pode ser um pouco impreciso em tamanho,
        # mas é a forma mais fácil de dividir sem reencodar todo o arquivo múltiplas vezes.
        # `-f segment` e `-segment_times` seriam mais precisos, mas um pouco mais complexos.
        # `-map 0` mapeia todos os streams de entrada para saída
        # `-c copy` tenta copiar os streams sem re-encodificar para velocidade,
        # mas pode não ser possível se a divisão cair no meio de um frame ou se o codec não suportar.
        # Se for preciso re-encodificar (ex: para garantir WebM e controle de bitrate), mude `-c copy`
        # para `-c:a libopus -b:a 64k` (ou outro codec/bitrate).
        # Por simplicidade e velocidade, tentaremos `-c copy` primeiro.
        
        # Se você quer garantir a saída em WEBM e um tamanho aproximado, é melhor re-encodificar.
        # Vamos usar re-encodificação para garantir consistência e controle de tamanho.
        ffmpeg_split_command = [
            'ffmpeg',
            '-i', input_filepath,       # Arquivo de entrada
            '-map', '0',                # Mapeia todos os streams (áudio)
            '-f', 'segment',            # Usa o muxer de segmento
            '-segment_time', str(600), # Divide por tempo
            '-c:a', 'libopus',          # Codec de áudio para WebM (garantir formato)
            '-b:a', '64k',              # Bitrate para controlar tamanho
            '-vbr', 'on',               # VBR para Opus
            '-compression_level', '10', # Nível de compressão
            output_filename_pattern     # Padrão de nome de arquivo de saída
        ]

        logger.info(f"Executando FFmpeg split: {' '.join(ffmpeg_split_command)}")
        subprocess.run(ffmpeg_split_command, check=True, capture_output=True, text=True)
        logger.info(f"FFmpeg split concluído no diretório temporário: {temp_dir}")

        # 4. Ler os arquivos divididos para io.BytesIO
        for filename in sorted(os.listdir(temp_dir)):
            chunk_filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(chunk_filepath):
                with open(chunk_filepath, 'rb') as f:
                    chunk_buffer = io.BytesIO(f.read())
                    chunk_buffers.append(chunk_buffer)
                logger.debug(f"Lido chunk {filename} para buffer em memória (tamanho: {chunk_buffer.getbuffer().nbytes / (1024*1024):.2f}MB).")
        
        if not chunk_buffers:
            logger.warning(f"FFmpeg não gerou nenhum chunk para {input_filepath}.")
            return None

        return chunk_buffers

    except subprocess.CalledProcessError as e:
        logger.error(f"Erro FFmpeg/ffprobe ao dividir áudio: {e.stderr}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao dividir áudio em chunks: {e}", exc_info=True)
        return None
    finally:
        # Limpar o diretório temporário e seus conteúdos
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Diretório temporário {temp_dir} e seus conteúdos removidos.")