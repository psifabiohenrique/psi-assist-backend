class AudioRecorderUI {
    constructor() {
        this.isInitialized = false;
        this.selectedDeviceId = null;
        this.captureSystemAudio = false;
        this.recordingStartTime = null;
        this.timerInterval = null;
    }

    // Inicializa a interface
    async init() {
        if (this.isInitialized) return;

        // Verifica se o navegador suporta gravação
        if (!AudioRecorder.isSupported()) {
            this.showError('Seu navegador não suporta gravação de áudio.');
            return;
        }

        try {
            // Carrega os dispositivos de áudio
            await this.loadAudioDevices();
            this.setupEventListeners();
            this.isInitialized = true;
        } catch (error) {
            console.error('Erro ao inicializar interface:', error);
            this.showError('Erro ao acessar dispositivos de áudio. Verifique as permissões.');
        }
    }

    // Carrega e popula a lista de dispositivos de áudio
    async loadAudioDevices() {
        const devices = await window.audioRecorder.getAudioDevices();
        const deviceSelect = document.getElementById('audio-device-select');

        // Limpa opções existentes
        deviceSelect.innerHTML = '<option value="">Microfone padrão</option>';

        // Adiciona cada dispositivo
        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.textContent = device.label || `Microfone ${device.deviceId.substring(0, 8)}`;
            deviceSelect.appendChild(option);
        });
    }

    // Configura os event listeners
    setupEventListeners() {
        // Seleção de dispositivo
        document.getElementById('audio-device-select').addEventListener('change', (e) => {
            this.selectedDeviceId = e.target.value || null;
        });

        // Checkbox para capturar áudio do sistema
        document.getElementById('capture-system-audio').addEventListener('change', (e) => {
            this.captureSystemAudio = e.target.checked;
        });

        // Botões de controle
        document.getElementById('start-recording-btn').addEventListener('click', () => {
            this.startRecording();
        });

        document.getElementById('stop-recording-btn').addEventListener('click', () => {
            this.stopRecording();
        });

        document.getElementById('cancel-recording-btn').addEventListener('click', () => {
            this.cancelRecording();
        });
    }

    // Inicia a gravação
    async startRecording() {
        try {
            this.showStatus('Iniciando gravação...', 'info');

            await window.audioRecorder.startRecording(this.selectedDeviceId, this.captureSystemAudio);

            this.recordingStartTime = Date.now();
            this.updateUIForRecording();
            this.startTimer();
            this.showStatus('Gravando...', 'recording');

        } catch (error) {
            console.error('Erro ao iniciar gravação:', error);
            this.showError('Erro ao iniciar gravação. Verifique as permissões de microfone.');
            this.resetUI();
        }
    }

    // Para a gravação
    stopRecording() {
        window.audioRecorder.stopRecording();
        this.stopTimer();
        this.showStatus('Finalizando gravação...', 'info');

        // Aguarda um pouco para o blob ser criado
        setTimeout(() => {
            this.updateUIForStopped();
            this.showStatus('Gravação finalizada!', 'success');

            // Inicia o download e submissão
            window.audioSubmitter.handleRecordingComplete();
        }, 500);
    }

    // Cancela a gravação
    cancelRecording() {
        window.audioRecorder.cancelRecording();
        this.stopTimer();
        this.resetUI();
        this.showStatus('Gravação cancelada.', 'info');
    }

    // Atualiza a interface para o estado de gravação
    updateUIForRecording() {
        document.getElementById('recording-controls').style.display = 'none';
        document.getElementById('recording-active').style.display = 'block';
        document.getElementById('recording-controls').classList.add('hidden');
        document.getElementById('recording-active').classList.remove('hidden');
        document.getElementById('audio-device-select').disabled = true;
        document.getElementById('capture-system-audio').disabled = true;

        // Desabilita o botão de salvar normal durante gravação
        const normalSubmitBtn = document.querySelector('form[method="post"] button[type="submit"]');
        if (normalSubmitBtn) {
            normalSubmitBtn.disabled = true;
        }
    }

    // Atualiza a interface para o estado parado
    updateUIForStopped() {
        document.getElementById('recording-active').style.display = 'none';
        document.getElementById('recording-complete').style.display = 'block';

        // Reabilita o botão de salvar normal após finalizar gravação
        const normalSubmitBtn = document.querySelector('form[method="post"] button[type="submit"]');
        if (normalSubmitBtn) {
            normalSubmitBtn.disabled = false;
        }
    }

    // Reseta a interface para o estado inicial
    resetUI() {
        document.getElementById('recording-controls').style.display = 'block';
        document.getElementById('recording-active').style.display = 'none';
        document.getElementById('recording-complete').style.display = 'none';
        document.getElementById('audio-device-select').disabled = false;
        document.getElementById('capture-system-audio').disabled = false;
        document.getElementById('recording-timer').textContent = '00:00';

        // Reabilita o botão de salvar normal
        const normalSubmitBtn = document.querySelector('form[method="post"] button[type="submit"]');
        if (normalSubmitBtn) {
            normalSubmitBtn.disabled = false;
        }

        this.showStatus('Pronto para gravar.', 'ready');
    }

    // Inicia o timer de gravação
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            document.getElementById('recording-timer').textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    // Para o timer
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // Mostra mensagem de status
    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('recording-status');
        statusElement.textContent = message;
        statusElement.className = `recording-status ${type}`;
    }

    // Mostra mensagem de erro
    showError(message) {
        this.showStatus(message, 'error');
    }
}

// Inicializa a interface quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', async () => {
    window.audioRecorderUI = new AudioRecorderUI();
    await window.audioRecorderUI.init();
});