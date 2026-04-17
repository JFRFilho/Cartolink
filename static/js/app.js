/**
 * CartLink - Frontend Application
 * Handles file selection, upload, status polling, and UI state management.
 */

// ── State ─────────────────────────────────────────────────────
let selectedFile = null;
let currentUploadId = null;
let pollingInterval = null;
let currentLink = null;

// Step order for visual progress
const STEP_ORDER = ['saving', 'uploading', 'processing', 'permissions', 'done'];

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupDropZone();
  setupFileInput();
  loadHistory();
});

// ── File Input ────────────────────────────────────────────────
function setupFileInput() {
  const input = document.getElementById('fileInput');
  if (!input) return;
  input.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  selectedFile = file;
  enableUploadButton();
  resetStatus();

  try {
    showFilePreview(file);
  } catch (err) {
    console.error('Erro ao exibir preview do arquivo:', err);
  }
}

function showFilePreview(file) {
  const preview = document.getElementById('filePreview');
  const nameEl = document.getElementById('fileName');
  const sizeEl = document.getElementById('fileSize');
  const iconEl = document.getElementById('fileTypeIcon');

  if (nameEl) {
    nameEl.textContent = file.name;
  }

  if (sizeEl) {
    sizeEl.textContent = formatFileSize(file.size) + ' · ' + (file.type || 'Tipo desconhecido');
  }

  if (iconEl) {
    const ext = file.name.includes('.') ? file.name.split('.').pop().toLowerCase() : '';
    const iconColor = getIconColor(ext);
    iconEl.style.background = iconColor.bg;

    const iconInner = iconEl.querySelector('i');
    if (iconInner) {
      iconInner.style.color = iconColor.color;
    }
  }

  if (preview) {
    preview.classList.remove('hidden');
    preview.classList.add('fade-in-up');
  }
}

function clearFile() {
  selectedFile = null;

  const fileInput = document.getElementById('fileInput');
  const filePreview = document.getElementById('filePreview');

  if (fileInput) fileInput.value = '';
  if (filePreview) filePreview.classList.add('hidden');

  disableUploadButton();
}

// ── Drop Zone ─────────────────────────────────────────────────
function setupDropZone() {
  const zone = document.getElementById('dropZone');
  if (!zone) return;

  zone.addEventListener('dragenter', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  zone.addEventListener('dragleave', (e) => {
    if (!zone.contains(e.relatedTarget)) {
      zone.classList.remove('drag-over');
    }
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });
}

// ── Upload ────────────────────────────────────────────────────
async function startUpload() {
  if (!selectedFile) return;

  // UI: disable controls during upload
  setUploadingState(true);
  hideResultCards();
  resetStatus();

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    setStatusLabel('Iniciando upload...');

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Erro ao iniciar upload.');
    }

    currentUploadId = data.upload_id;
    startPolling(currentUploadId);

  } catch (err) {
    showError(err.message);
    setUploadingState(false);
  }
}

// ── Status Polling ────────────────────────────────────────────
function startPolling(uploadId) {
  if (pollingInterval) clearInterval(pollingInterval);

  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${uploadId}`);
      const status = await res.json();

      updateUI(status);

      if (status.status === 'done' || status.status === 'error') {
        clearInterval(pollingInterval);
        pollingInterval = null;
        setUploadingState(false);
      }
    } catch (err) {
      clearInterval(pollingInterval);
      showError('Erro de comunicação com o servidor.');
      setUploadingState(false);
    }
  }, 800);
}

function updateUI(status) {
  const { status: step, message, progress, link, error } = status;

  // Progress bar
  setProgress(progress || 0);
  setStatusLabel(message || '');

  // Step indicators
  updateSteps(step);

  if (step === 'done' && link) {
    showResult(link, status.file_name);
  } else if (step === 'error') {
    showError(error || message);
  }
}

// ── Step Indicators ───────────────────────────────────────────
function updateSteps(currentStep) {
  const items = document.querySelectorAll('.step-item');
  const currentIndex = STEP_ORDER.indexOf(currentStep);
  const isFinished = currentStep === 'done';

  items.forEach((item) => {
    const step = item.dataset.step;
    const stepIndex = STEP_ORDER.indexOf(step);

    item.removeAttribute('data-active');
    item.removeAttribute('data-done');
    item.removeAttribute('data-error');

    if (currentStep === 'error') {
      if (stepIndex < currentIndex) {
        item.setAttribute('data-done', 'true');
      } else if (stepIndex === currentIndex) {
        item.setAttribute('data-error', 'true');
      }
    } else {
      if (stepIndex < currentIndex || (isFinished && stepIndex === currentIndex)) {
        item.setAttribute('data-done', 'true');
      } else if (stepIndex === currentIndex) {
        item.setAttribute('data-active', 'true');
      }
    }
  });

  // Re-create icons after attribute changes (Lucide)
  lucide.createIcons();
}

// ── Progress ──────────────────────────────────────────────────
function setProgress(percent) {
  const bar = document.getElementById('progressBar');
  const label = document.getElementById('progressPercent');
  if (bar) bar.style.width = percent + '%';
  if (label) label.textContent = percent + '%';
}

function setStatusLabel(msg) {
  const el = document.getElementById('statusLabel');
  if (el) el.textContent = msg;
}

// ── Result ────────────────────────────────────────────────────
function showResult(link, fileName) {
  currentLink = link;

  const resultCard = document.getElementById('resultCard');
  const linkEl = document.getElementById('resultLink');
  const openEl = document.getElementById('openLink');

  if (resultCard) {
    resultCard.classList.remove('hidden');
    resultCard.classList.add('fade-in-up');
  }
  if (linkEl) linkEl.textContent = link;
  if (openEl) openEl.href = link;

  // Save to history
  saveHistory(fileName || selectedFile?.name || 'Arquivo', link);

  // Reset file selection
  clearFile();
}

function showError(message) {
  const errorCard = document.getElementById('errorCard');
  const errorMsg = document.getElementById('errorMessage');

  if (errorCard) {
    errorCard.classList.remove('hidden');
    errorCard.classList.add('fade-in-up');
  }
  if (errorMsg) errorMsg.textContent = message;

  setProgress(0);
  setStatusLabel('Erro no processo');
}

function hideResultCards() {
  document.getElementById('resultCard')?.classList.add('hidden');
  document.getElementById('errorCard')?.classList.add('hidden');
}

// ── Copy Link ─────────────────────────────────────────────────
async function copyLink() {
  if (!currentLink) return;

  try {
    await navigator.clipboard.writeText(currentLink);
    const btn = document.getElementById('copyBtn');
    const text = document.getElementById('copyText');

    btn.classList.add('copy-success');
    text.textContent = '✓ Link Copiado!';

    setTimeout(() => {
      btn.classList.remove('copy-success');
      text.textContent = 'Copiar Link';
    }, 2000);
  } catch (err) {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = currentLink;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
}

// ── UI State ──────────────────────────────────────────────────
function setUploadingState(isUploading) {
  const btn = document.getElementById('uploadBtn');
  const dropZone = document.getElementById('dropZone');

  if (btn) {
    btn.disabled = isUploading || !selectedFile;
    btn.innerHTML = isUploading
      ? '<svg class="spin-slow w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Enviando...'
      : '<i data-lucide="send" class="w-4 h-4"></i> Transformar Arquivo';
  }

  if (dropZone) {
    dropZone.style.pointerEvents = isUploading ? 'none' : 'auto';
    dropZone.style.opacity = isUploading ? '0.5' : '1';
  }

  if (!isUploading) lucide.createIcons();
}

function enableUploadButton() {
  const btn = document.getElementById('uploadBtn');
  if (btn) btn.disabled = false;
}

function disableUploadButton() {
  const btn = document.getElementById('uploadBtn');
  if (btn) btn.disabled = true;
}

function resetStatus() {
  setProgress(0);
  setStatusLabel('Aguardando envio');
  document.querySelectorAll('.step-item').forEach(item => {
    item.removeAttribute('data-active');
    item.removeAttribute('data-done');
    item.removeAttribute('data-error');
  });
  lucide.createIcons();
}

function resetUpload() {
  clearFile();
  resetStatus();
  hideResultCards();
  currentUploadId = null;
  currentLink = null;
}

// ── History ───────────────────────────────────────────────────
function saveHistory(fileName, link) {
  const history = {
    fileName,
    link,
    timestamp: new Date().toISOString()
  };
  localStorage.setItem('cartlink_last', JSON.stringify(history));
  renderHistory(history);
}

function loadHistory() {
  const saved = localStorage.getItem('cartlink_last');
  if (saved) {
    try {
      renderHistory(JSON.parse(saved));
    } catch (e) {}
  }
}

function renderHistory(data) {
  const section = document.getElementById('historySection');
  const nameEl = document.getElementById('historyFileName');
  const timeEl = document.getElementById('historyTime');
  const linkEl = document.getElementById('historyLink');

  if (!section) return;

  section.classList.remove('hidden');
  section.classList.add('fade-in-up');

  if (nameEl) nameEl.textContent = data.fileName;
  if (linkEl) linkEl.href = data.link;

  if (timeEl && data.timestamp) {
    const d = new Date(data.timestamp);
    timeEl.textContent = d.toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }
}

function clearHistory() {
  localStorage.removeItem('cartlink_last');
  document.getElementById('historySection')?.classList.add('hidden');
}

// ── Utilities ─────────────────────────────────────────────────
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getIconColor(ext) {
  const colorMap = {
    pdf: { bg: 'rgba(240, 64, 96, 0.15)', color: '#f04060' },
    doc: { bg: 'rgba(30, 79, 216, 0.15)', color: '#4b7cf3' },
    docx: { bg: 'rgba(30, 79, 216, 0.15)', color: '#4b7cf3' },
    xls: { bg: 'rgba(16, 201, 122, 0.15)', color: '#10c97a' },
    xlsx: { bg: 'rgba(16, 201, 122, 0.15)', color: '#10c97a' },
    ppt: { bg: 'rgba(245, 166, 35, 0.15)', color: '#f5a623' },
    pptx: { bg: 'rgba(245, 166, 35, 0.15)', color: '#f5a623' },
    jpg: { bg: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa' },
    jpeg: { bg: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa' },
    png: { bg: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa' },
    gif: { bg: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa' },
    zip: { bg: 'rgba(245, 166, 35, 0.15)', color: '#f5a623' },
    rar: { bg: 'rgba(245, 166, 35, 0.15)', color: '#f5a623' },
  };
  return colorMap[ext] || { bg: 'rgba(30, 79, 216, 0.15)', color: '#4b7cf3' };
}
