// Este script lida com toda a lógica para a aplicação de gravador de áudio.

// Objeto para simular um Enum, representando os diferentes estados da aplicação.
const RecordingState = {
  Idle: 'idle',
  RequestingPermissions: 'requesting_permissions',
  Recording: 'recording',
  Processing: 'processing',
  Finished: 'finished',
  Error: 'error',
};

// --- VARIÁVEIS DE ESTADO ---
let currentState = RecordingState.Idle;
let mediaRecorder = null;
let audioChunks = [];
let combinedStream = null;
let timerInterval = null;
let duration = 0;
let audioUrl = null;
let audioContext = null;
let supportedMimeType = ''; // Armazena o formato de áudio que o navegador suporta

// --- REFERÊNCIAS AOS ELEMENTOS DO DOM ---
const idleView = document.getElementById('idle-view');
const recordingView = document.getElementById('recording-view');
const processingView = document.getElementById('processing-view');
const finishedView = document.getElementById('finished-view');
const errorView = document.getElementById('error-view');
const includeMicCheck = document.getElementById('includeMic');
const micSelectionContainer = document.getElementById('mic-selection-container');
const micSelect = document.getElementById('mic-select');
const includeSystemCheck = document.getElementById('includeSystem');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const cancelBtn = document.getElementById('cancel-btn');
const timerDisplay = document.getElementById('timer');
const errorMessage = document.getElementById('error-message');
const tryAgainBtn = document.getElementById('try-again-btn');
const audioPlayer = document.getElementById('audio-player');
const playPauseBtn = document.getElementById('play-pause-btn');
const playIcon = document.getElementById('play-icon');
const pauseIcon = document.getElementById('pause-icon');
const progressBar = document.getElementById('progress-bar');
const downloadLink = document.getElementById('download-link');
const downloadFormatText = document.getElementById('download-format-text');
const processingFormatText = document.getElementById('processing-format-text');
const recordAgainBtn = document.getElementById('record-again-btn');
const micIconIdle = document.getElementById('mic-icon-idle');
const systemIconIdle = document.getElementById('system-icon-idle');

// --- FUNÇÕES DE ATUALIZAÇÃO DA UI ---

/**
 * Função central para atualizar a interface do usuário com base no estado atual.
 */
function updateUI() {
  idleView.classList.add('hidden');
  recordingView.classList.add('hidden');
  processingView.classList.add('hidden');
  finishedView.classList.add('hidden');
  errorView.classList.add('hidden');

  switch (currentState) {
    case RecordingState.Recording:
      recordingView.classList.remove('hidden');
      break;
    case RecordingState.Processing:
      processingView.classList.remove('hidden');
      break;
    case RecordingState.Finished:
      finishedView.classList.remove('hidden');
      break;
    case RecordingState.Error:
      errorView.classList.remove('hidden');
      break;
    case RecordingState.Idle:
    default:
      idleView.classList.remove('hidden');
      break;
  }
}

/**
 * Formata o tempo em segundos para o formato MM:SS.
 */
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// --- LÓGICA DE GRAVAÇÃO E ÁUDIO ---

/**
 * **MUDANÇA CRÍTICA:** Verifica qual formato de áudio o navegador suporta.
 * Isso evita o erro 'NotSupportedError' ao se adaptar ao ambiente do usuário.
 * Navegadores baseados em Chromium (Chrome, Edge) preferem 'webm', enquanto o Firefox pode preferir 'ogg'.
 */
function findSupportedMimeType() {
  const possibleTypes = [
    'audio/webm; codecs=opus',
    'audio/ogg; codecs=opus',
    'audio/webm',
    'audio/ogg',
    'audio/mp4', // Fallback
  ];
  return possibleTypes.find(type => MediaRecorder.isTypeSupported(type)) || '';
}


/**
 * Pede permissão e lista os dispositivos de microfone disponíveis.
 */
async function getMicDevices() {
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    const devices = await navigator.mediaDevices.enumerateDevices();
    const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
    
    micSelect.innerHTML = '';
    if (audioInputDevices.length > 0) {
      audioInputDevices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.deviceId;
        option.textContent = device.label || `Microfone ${micSelect.options.length + 1}`;
        micSelect.appendChild(option);
      });
      micSelectionContainer.classList.remove('hidden');
    } else {
      micSelectionContainer.classList.add('hidden');
      includeMicCheck.checked = false;
    }
  } catch (err) {
    console.error("Erro ao obter dispositivos de microfone:", err);
    showError("O acesso ao microfone é necessário. Por favor, conceda a permissão.");
  }
}

/**
 * Inicia o processo de gravação.
 */
async function startRecording() {
  if (!includeMicCheck.checked && !includeSystemCheck.checked) {
    showError("Por favor, selecione pelo menos uma fonte de áudio.");
    return;
  }
  
  // Verifica o suporte ao formato ANTES de qualquer outra coisa.
  supportedMimeType = findSupportedMimeType();
  if (!supportedMimeType) {
    showError("Seu navegador não suporta nenhum formato de gravação de áudio adequado.");
    return;
  }

  currentState = RecordingState.RequestingPermissions;
  cleanup();

  try {
    audioContext = new AudioContext();
    const destination = audioContext.createMediaStreamDestination();
    combinedStream = destination.stream;

    if (includeMicCheck.checked) {
      const micStream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: { exact: micSelect.value } }
      });
      const micSource = audioContext.createMediaStreamSource(micStream);
      micSource.connect(destination);
    }

    if (includeSystemCheck.checked) {
      const systemStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });
      const systemAudioTrack = systemStream.getAudioTracks()[0];
      if (!systemAudioTrack) {
        throw new Error("A fonte de exibição selecionada não fornece áudio.");
      }
      const systemAudioStream = new MediaStream([systemAudioTrack]);
      const systemSource = audioContext.createMediaStreamSource(systemAudioStream);
      systemSource.connect(destination);
      systemStream.getVideoTracks().forEach(track => track.stop());
    }

    if (combinedStream.getAudioTracks().length === 0) {
      throw new Error("Nenhuma faixa de áudio disponível para gravar.");
    }
    
    // Usa o formato que descobrimos ser compatível.
    const options = { mimeType: supportedMimeType };
    mediaRecorder = new MediaRecorder(combinedStream, options);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = handleRecordingStop;

    mediaRecorder.start();
    currentState = RecordingState.Recording;
    updateUI();

    duration = 0;
    timerDisplay.textContent = formatTime(duration);
    timerInterval = setInterval(() => {
      duration++;
      timerDisplay.textContent = formatTime(duration);
    }, 1000);

  } catch (err) {
    console.error("Erro ao iniciar a gravação:", err);
    showError(err instanceof Error ? err.message : "Ocorreu um erro desconhecido.");
    cleanup();
  }
}

/**
 * Lida com o fim da gravação e finaliza o arquivo de áudio.
 */
function handleRecordingStop() {
  currentState = RecordingState.Processing;
  const fileExtension = supportedMimeType.split('/')[1].split(';')[0];
  processingFormatText.textContent = `Finalizando sua gravação no formato ${fileExtension.toUpperCase()}.`
  updateUI();
  if (timerInterval) clearInterval(timerInterval);

  const audioBlob = new Blob(audioChunks, { type: supportedMimeType });
  audioUrl = URL.createObjectURL(audioBlob);

  audioPlayer.src = audioUrl;
  downloadLink.href = audioUrl;
  downloadFormatText.textContent = fileExtension.toUpperCase();
  downloadLink.download = `gravacao-${new Date().toISOString()}.${fileExtension}`;
  
  currentState = RecordingState.Finished;
  updateUI();

  cleanup();
}

/**
 * Para a gravação. O evento 'onstop' cuidará do resto.
 */
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
}

/**
 * Cancela a gravação e descarta os dados.
 */
function cancelRecording() {
  if (window.confirm("Tem certeza que deseja cancelar a gravação? Todos os dados gravados serão perdidos.")) {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.onstop = null;
        mediaRecorder.stop();
    }
    cleanup();
    if (timerInterval) clearInterval(timerInterval);
    reset();
  }
}

/**
 * Limpa todos os recursos de gravação.
 */
function cleanup() {
  if (combinedStream) {
    combinedStream.getTracks().forEach(track => track.stop());
    combinedStream = null;
  }
  if (mediaRecorder) {
    mediaRecorder.ondataavailable = null;
    mediaRecorder.onstop = null;
    mediaRecorder = null;
  }
  if (audioContext && audioContext.state !== 'closed') {
    audioContext.close().catch(console.error);
  }
  audioChunks = [];
}

/**
 * Reseta o estado da aplicação para o início.
 */
function reset() {
  if (audioUrl) {
    URL.revokeObjectURL(audioUrl);
    audioUrl = null;
  }
  duration = 0;
  currentState = RecordingState.Idle;
  updateUI();
}

/**
 * Mostra uma mensagem de erro na UI.
 */
function showError(message) {
  errorMessage.textContent = message;
  currentState = RecordingState.Error;
  updateUI();
}

// --- CONFIGURAÇÃO DE EVENT LISTENERS ---

function setupEventListeners() {
  startBtn.addEventListener('click', startRecording);
  stopBtn.addEventListener('click', stopRecording);
  cancelBtn.addEventListener('click', cancelRecording);
  tryAgainBtn.addEventListener('click', reset);
  recordAgainBtn.addEventListener('click', reset);

  includeMicCheck.addEventListener('change', () => {
    micSelectionContainer.style.display = includeMicCheck.checked ? 'block' : 'none';
    micIconIdle.classList.toggle('text-cyan-400', includeMicCheck.checked);
    micIconIdle.classList.toggle('text-gray-400', !includeMicCheck.checked);
    startBtn.disabled = !includeMicCheck.checked && !includeSystemCheck.checked;
  });

  includeSystemCheck.addEventListener('change', () => {
    systemIconIdle.classList.toggle('text-cyan-400', includeSystemCheck.checked);
    systemIconIdle.classList.toggle('text-gray-400', !includeSystemCheck.checked);
    startBtn.disabled = !includeMicCheck.checked && !includeSystemCheck.checked;
  });
  
  playPauseBtn.addEventListener('click', () => {
    if (audioPlayer.paused) {
      audioPlayer.play();
    } else {
      audioPlayer.pause();
    }
  });

  audioPlayer.addEventListener('play', () => {
    playIcon.classList.add('hidden');
    pauseIcon.classList.remove('hidden');
  });

  audioPlayer.addEventListener('pause', () => {
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
  });
  
  audioPlayer.addEventListener('ended', () => {
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
    progressBar.style.width = '0%';
  });

  audioPlayer.addEventListener('timeupdate', () => {
    if (audioPlayer.duration > 0) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressBar.style.width = `${progress}%`;
    }
  });
}

/**
 * Função de inicialização da aplicação.
 */
function init() {
  setupEventListeners();
  getMicDevices();
  updateUI();
  startBtn.disabled = !includeMicCheck.checked && !includeSystemCheck.checked;
}

document.addEventListener('DOMContentLoaded', init);
