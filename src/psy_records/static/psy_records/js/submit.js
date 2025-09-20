class AudioSubmitter {
    constructor() {
        this.originalForm = null;
        this.audioFile = null;
        this.hasAudio = false;
    }

    // Inicializa o submitter
    init() {
        this.originalForm = document.querySelector('form[method="post"]');
        if (!this.originalForm) {
            console.error('Formulário não encontrado');
            return;
        }

        // Intercepta o submit original do formulário
        this.originalForm.addEventListener('submit', (e) => {
            // Se há áudio gravado, previne submit normal e processa com áudio
            if (this.hasAudio && this.audioFile) {
                e.preventDefault();
                this.submitWithAudio();
                return;
            }

            // Se não há áudio, permite submit normal (modo texto apenas)
            // O Django processará normalmente
        });
    }

    // Chamado quando a gravação é finalizada
    handleRecordingComplete() {
        const audioBlob = window.audioRecorder.getAudioBlob();
        if (!audioBlob) {
            console.error('Nenhum áudio gravado encontrado');
            return;
        }

        // Criar nome do arquivo: `${Nome do paciente} - ${Data}.ext`
        const patientName = document.getElementById("patient-name").textContent.trim();
        const now = new Date();
        const dateString = `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, "0")}-${now.getDate().toString().padStart(2, "0")}`;

        const fileName = `${patientName} - ${dateString}`;

        // Cria o arquivo para download
        this.audioFile = window.audioRecorder.createDownloadFile(fileName);
        this.hasAudio = true;

        // Inicia o download automático
        this.downloadAudio();

        // Mostra opção de submeter formulário
        this.showSubmitOption();
    }

    // Faz o download do áudio gravado
    downloadAudio() {
        if (!this.audioFile) return;

        const url = URL.createObjectURL(this.audioFile);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.audioFile.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('Download do áudio iniciado:', this.audioFile.name);
    }

    // Mostra a opção de submeter o formulário
    showSubmitOption() {
        const submitSection = document.getElementById('submit-with-audio');
        if (submitSection) {
            submitSection.style.display = 'block';
        }

        // Adiciona event listener para o botão de submit com áudio
        const submitBtn = document.getElementById('submit-with-audio-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitWithAudio();
            });
        }
    }

    // Submete o formulário com o áudio
    async submitWithAudio() {
        if (!this.audioFile || !this.originalForm) {
            console.error('Arquivo de áudio ou formulário não encontrado');
            return;
        }

        try {
            // Mostra loading
            this.showSubmitStatus('Enviando dados para processamento com IA...', 'loading');

            // Cria FormData com todos os dados do formulário
            const formData = new FormData(this.originalForm);

            // Adiciona o arquivo de áudio
            formData.append('audio_file', this.audioFile);

            // Adiciona flag indicando que há áudio
            formData.append('has_audio', 'true');

            // Envia via fetch
            const response = await fetch(this.originalForm.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                // Se a resposta for um redirect, segue o redirect
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                // Se retornou JSON, processa a resposta
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const result = await response.json();
                    this.handleSubmitResponse(result);
                } else {
                    // Se retornou HTML, substitui a página
                    const html = await response.text();
                    document.open();
                    document.write(html);
                    document.close();
                }
            } else {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

        } catch (error) {
            console.error('Erro ao enviar formulário:', error);
            this.showSubmitStatus('Erro ao enviar dados. Tente novamente.', 'error');
        }
    }

    // Processa a resposta do submit
    handleSubmitResponse(response) {
        if (response.success) {
            this.showSubmitStatus('Prontuário processado e salvo com sucesso!', 'success');

            // Redireciona após um tempo
            setTimeout(() => {
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                } else {
                    // Fallback: volta para a página do paciente
                    window.history.back();
                }
            }, 2000);
        } else {
            this.showSubmitStatus(response.message || 'Erro ao processar dados.', 'error');
        }
    }

    // Permite submit sem áudio (formulário normal)
    submitWithoutAudio() {
        // Remove o áudio e submete normalmente
        this.audioFile = null;
        this.hasAudio = false;

        // Reseta a interface de gravação
        window.audioRecorderUI.resetUI();

        // Submete o formulário normalmente
        this.originalForm.submit();
    }

    // Mostra status do envio
    showSubmitStatus(message, type = 'info') {
        const statusElement = document.getElementById('submit-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `submit-status ${type}`;
            statusElement.style.display = 'block';
        }
    }
}

// Inicializa quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    window.audioSubmitter = new AudioSubmitter();
    window.audioSubmitter.init();
});