class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.audioBlob = null;
    }

    // Lista os dispositivos de áudio disponíveis
    async getAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'audioinput');
        } catch (error) {
            console.error('Erro ao listar dispositivos de áudio:', error);
            return [];
        }
    }

    // Inicia a gravação com o dispositivo selecionado
    async startRecording(deviceId = null, captureSystemAudio = false) {
        try {
            // Configurações de captura de áudio
            const constraints = {
                audio: {
                    deviceId: deviceId ? { exact: deviceId } : undefined,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            };

            // Se quiser capturar áudio do sistema também (limitado pelo navegador)
            if (captureSystemAudio) {
                try {
                    // Tenta capturar áudio do sistema (funciona apenas em alguns navegadores)
                    const displayStream = await navigator.mediaDevices.getDisplayMedia({
                        video: true,
                        audio: true
                    });
                    displayStream.getVideoTracks().forEach(track => track.stop());
                    // Combina microfone + áudio do sistema
                    const micStream = await navigator.mediaDevices.getUserMedia(constraints);
                    this.stream = this.combineAudioStreams(micStream, displayStream);
                } catch (systemAudioError) {
                    console.warn('Não foi possível capturar áudio do sistema, usando apenas microfone:', systemAudioError);
                    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
                }
            } else {
                this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            }

            // Configura o MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: this.getSupportedMimeType()
            });

            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.audioBlob = new Blob(this.audioChunks, { 
                    type: this.mediaRecorder.mimeType 
                });
                this.stopStream();
            };

            this.mediaRecorder.start(1000); // Coleta dados a cada 1 segundo
            this.isRecording = true;

            return true;
        } catch (error) {
            console.error('Erro ao iniciar gravação:', error);
            throw error;
        }
    }

    // Para a gravação
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
    }

    // Cancela a gravação
    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
        this.audioChunks = [];
        this.audioBlob = null;
        this.stopStream();
    }

    // Para o stream de áudio
    stopStream() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    // Combina múltiplos streams de áudio
    combineAudioStreams(micStream, systemStream) {
        const audioContext = new AudioContext();
        const micSource = audioContext.createMediaStreamSource(micStream);
        const systemSource = audioContext.createMediaStreamSource(systemStream);
        const destination = audioContext.createMediaStreamDestination();

        micSource.connect(destination);
        systemSource.connect(destination);

        return destination.stream;
    }

    // Retorna o tipo MIME suportado pelo navegador
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/ogg;codecs=opus',
            'audio/ogg'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return 'audio/webm'; // fallback
    }

    // Retorna o blob do áudio gravado
    getAudioBlob() {
        return this.audioBlob;
    }

    // Cria um arquivo para download
    createDownloadFile(filename = 'gravacao') {
        if (!this.audioBlob) return null;

        const extension = this.getFileExtension();
        const safeName = filename.replace(/[/\\?%*:|"<>]/g, '-'); // remove caracteres inválidos
        const file = new File([this.audioBlob], `${safeName}.${extension}`, {
            type: this.audioBlob.type
        });
        return file;
    }

    // Retorna a extensão do arquivo baseada no tipo MIME
    getFileExtension() {
        if (!this.audioBlob) return 'webm';
        
        const type = this.audioBlob.type;
        if (type.includes('mp4')) return 'mp4';
        if (type.includes('ogg')) return 'ogg';
        return 'webm';
    }

    // Verifica se o navegador suporta gravação de áudio
    static isSupported() {
        return !!(navigator.mediaDevices && 
                 navigator.mediaDevices.getUserMedia && 
                 window.MediaRecorder);
    }
}

// Instância global do recorder
window.audioRecorder = new AudioRecorder();