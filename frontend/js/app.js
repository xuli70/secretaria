const API = '';

const $ = (sel) => document.querySelector(sel);

const screens = {
    login: $('#screen-login'),
    chat: $('#screen-chat'),
};

function showScreen(name) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[name].classList.add('active');
}

// --- Auth helpers ---

function getToken() {
    return localStorage.getItem('token');
}

function getUser() {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
}

function saveAuth(data) {
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify({ id: data.user_id, username: data.username }));
}

function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// --- API helpers ---

function authHeaders() {
    const h = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
}

function authUrl(url) {
    const t = getToken();
    return t ? url + '?token=' + encodeURIComponent(t) : url;
}

async function apiPost(path, body) {
    const res = await fetch(API + path, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(body),
    });
    if (res.status === 401) { clearAuth(); showScreen('login'); throw new Error('Sesion expirada'); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error del servidor');
    return data;
}

async function apiGet(path) {
    const res = await fetch(API + path, { headers: authHeaders() });
    if (res.status === 401) { clearAuth(); showScreen('login'); throw new Error('Sesion expirada'); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error del servidor');
    return data;
}

async function apiDelete(path) {
    const res = await fetch(API + path, { method: 'DELETE', headers: authHeaders() });
    if (res.status === 401) { clearAuth(); showScreen('login'); throw new Error('Sesion expirada'); }
    if (!res.ok && res.status !== 204) {
        const data = await res.json();
        throw new Error(data.detail || 'Error del servidor');
    }
}

async function apiPatch(path, body) {
    const res = await fetch(API + path, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(body),
    });
    if (res.status === 401) { clearAuth(); showScreen('login'); throw new Error('Sesion expirada'); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error del servidor');
    return data;
}

// --- Login Form ---

const form = $('#form-login');
const btnLogin = $('#btn-login');
const errorEl = $('#login-error');

function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = false;
}

function hideError() {
    errorEl.hidden = true;
}

async function handleAuth(endpoint) {
    hideError();
    const username = $('#input-username').value.trim();
    const password = $('#input-password').value;

    if (!username || !password) {
        showError('Completa todos los campos');
        return;
    }

    btnLogin.disabled = true;

    try {
        const data = await apiPost(endpoint, { username, password });
        saveAuth(data);
        enterApp();
    } catch (err) {
        showError(err.message);
    } finally {
        btnLogin.disabled = false;
    }
}

form.addEventListener('submit', (e) => {
    e.preventDefault();
    handleAuth('/api/auth/login');
});

// --- Chat State ---

let currentConversationId = null;
let conversations = [];
let isStreaming = false;
let searchMode = false;
let docMode = false;

// --- File upload state ---
let pendingFile = null;     // File object from picker
let pendingFileId = null;   // file ID after upload completes
let isUploading = false;

// --- Telegram state ---
let telegramContacts = [];

// --- Google state ---
let googleConnected = false;

// --- File explorer state ---
let activeTab = 'conversations';
let explorerFiles = [];

// --- Selection mode state ---
let selectionMode = false;
let selectedMessageIds = new Set();

// --- DOM refs ---
const sidebar = $('#sidebar');
const sidebarOverlay = $('#sidebar-overlay');
const convList = $('#conv-list');
const chatMessages = $('#chat-messages');
const welcomeMsg = $('#welcome-msg');
const typingIndicator = $('#typing-indicator');
const inputBar = $('#input-bar');
const msgInput = $('#msg-input');
const btnSend = $('#btn-send');
const chatTitle = $('#chat-title');
const fileInput = $('#file-input');
const btnAttach = $('#btn-attach');
const attachmentPreview = $('#attachment-preview');
const attachmentPreviewName = $('#attachment-preview-name');
const attachmentPreviewSize = $('#attachment-preview-size');
const btnRemoveAttachment = $('#btn-remove-attachment');
const btnSearchToggle = $('#btn-search-toggle');
const btnDocToggle = $('#btn-doc-toggle');
const docFormatSelect = $('#doc-format-select');
const btnTelegram = $('#btn-telegram');
const telegramOverlay = $('#telegram-overlay');
const telegramModal = $('#telegram-modal');
const telegramContactsList = $('#telegram-contacts-list');
const telegramBotStatus = $('#telegram-bot-status');
const telegramAddForm = $('#telegram-add-form');
const selectionToolbar = $('#selection-toolbar');
const selectionCount = $('#selection-count');
const btnSelectionClose = $('#btn-selection-close');
const btnSelectionForward = $('#btn-selection-forward');
const toastContainer = $('#toast-container');
const btnGoogle = $('#btn-google');
const googleOverlay = $('#google-overlay');
const googleModal = $('#google-modal');
const googleDisconnected = $('#google-disconnected');
const googleConnectedSection = $('#google-connected');
const googleScopesList = $('#google-scopes-list');
const btnGoogleConnect = $('#btn-google-connect');
const btnGoogleDisconnect = $('#btn-google-disconnect');
const fileExplorer = $('#file-explorer');
const fileExplorerEmpty = $('#file-explorer-empty');
const sidebarTabs = document.querySelectorAll('.sidebar-tab');

// --- Sidebar toggle ---

function openSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('active');
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
}

$('#btn-menu').addEventListener('click', openSidebar);
sidebarOverlay.addEventListener('click', closeSidebar);

// --- Sidebar Tabs ---

sidebarTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        if (tabName === activeTab) return;
        activeTab = tabName;
        sidebarTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
        if (tabName === 'files') {
            convList.hidden = true;
            fileExplorer.hidden = false;
            sidebar.classList.add('files-active');
            loadExplorerFiles();
        } else {
            convList.hidden = false;
            fileExplorer.hidden = true;
            sidebar.classList.remove('files-active');
        }
    });
});

// --- File Explorer ---

async function loadExplorerFiles() {
    try {
        explorerFiles = await apiGet('/api/files');
        renderFileExplorer();
    } catch (err) {
        console.error('Error loading files:', err);
        showToast('Error cargando archivos');
    }
}

function renderFileExplorer() {
    const groups = { documents: [], images: [], generated: [] };

    explorerFiles.forEach(f => {
        if (f.is_generated) groups.generated.push(f);
        else if (f.file_type === 'image') groups.images.push(f);
        else groups.documents.push(f);
    });

    const totalFiles = explorerFiles.length;
    fileExplorerEmpty.hidden = totalFiles > 0;

    for (const [groupName, files] of Object.entries(groups)) {
        const groupEl = fileExplorer.querySelector(`[data-group="${groupName}"]`);
        if (!groupEl) continue;

        const badge = groupEl.querySelector('.file-group-badge');
        const itemsContainer = groupEl.querySelector('.file-group-items');

        badge.textContent = files.length;
        itemsContainer.innerHTML = '';

        if (files.length === 0) {
            groupEl.classList.add('hidden-group');
            groupEl.classList.remove('expanded');
        } else {
            groupEl.classList.remove('hidden-group');
            files.forEach(f => {
                const downloadUrl = f.is_generated
                    ? API + `/api/documents/${f.id}`
                    : API + `/api/upload/files/${f.id}`;
                const ext = f.filename.split('.').pop().toUpperCase();
                const metaParts = [ext, formatFileSize(f.size_bytes), formatDate(f.created_at)];
                if (!f.available && f.recoverable) metaParts.push('Recuperable');
                else if (!f.available) metaParts.push('No disponible');
                const meta = metaParts.filter(Boolean).join(' \u00b7 ');

                const canClick = f.available || f.recoverable;
                let itemClass = 'file-explorer-item';
                if (!f.available && f.recoverable) itemClass += ' recoverable';
                else if (!f.available) itemClass += ' unavailable';

                const item = document.createElement('div');
                item.className = itemClass;
                item.style.cursor = canClick ? 'pointer' : 'default';
                item.innerHTML = `
                    <div class="file-icon${f.is_generated ? ' generated' : ''}">${escapeHtml(ext)}</div>
                    <div class="file-explorer-item-info">
                        <div class="file-explorer-item-name">${escapeHtml(f.filename)}</div>
                        <div class="file-explorer-item-meta">${meta}</div>
                    </div>
                `;
                if (!canClick) { itemsContainer.appendChild(item); return; }
                item.addEventListener('click', async () => {
                    try {
                        const resp = await fetch(downloadUrl, {
                            headers: { 'Authorization': 'Bearer ' + getToken() },
                        });
                        if (!resp.ok) {
                            const err = await resp.json().catch(() => ({}));
                            showToast(err.detail || 'Error al descargar archivo');
                            return;
                        }
                        const blob = await resp.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = f.filename;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        URL.revokeObjectURL(blobUrl);
                        // Refresh explorer after successful download (file may now be available)
                        if (!f.available) loadExplorerFiles();
                    } catch (e) {
                        showToast('Error: ' + e.message);
                    }
                });
                itemsContainer.appendChild(item);
            });
        }
    }
}

// Collapse/expand file groups
fileExplorer.addEventListener('click', (e) => {
    const header = e.target.closest('.file-group-header');
    if (!header) return;
    const group = header.closest('.file-group');
    if (group) group.classList.toggle('expanded');
});

// --- Search toggle ---

btnSearchToggle.addEventListener('click', () => {
    searchMode = !searchMode;
    if (searchMode) { docMode = false; btnDocToggle.classList.remove('active'); docFormatSelect.hidden = true; }
    btnSearchToggle.classList.toggle('active', searchMode);
    updateInputPlaceholder();
});

btnDocToggle.addEventListener('click', () => {
    docMode = !docMode;
    if (docMode) { searchMode = false; btnSearchToggle.classList.remove('active'); }
    btnDocToggle.classList.toggle('active', docMode);
    docFormatSelect.hidden = !docMode;
    updateInputPlaceholder();
});

function updateInputPlaceholder() {
    if (docMode) msgInput.placeholder = 'Describe el documento a generar...';
    else if (searchMode) msgInput.placeholder = 'Busca en internet...';
    else msgInput.placeholder = 'Escribe un mensaje...';
}

// --- Conversations ---

async function loadConversations() {
    try {
        conversations = await apiGet('/api/chat/conversations');
        renderConversationList();
    } catch (err) {
        console.error('Error loading conversations:', err);
    }
}

function renderConversationList() {
    convList.innerHTML = '';
    conversations.forEach(conv => {
        const el = document.createElement('div');
        el.className = 'conv-item' + (conv.id === currentConversationId ? ' active' : '');
        el.innerHTML = `
            <div class="conv-item-info">
                <div class="conv-item-title">${escapeHtml(conv.title)}</div>
                <div class="conv-item-date">${formatDate(conv.updated_at)}</div>
            </div>
            <button class="conv-item-delete" title="Eliminar">&times;</button>
        `;
        el.querySelector('.conv-item-info').addEventListener('click', () => {
            selectConversation(conv.id);
            closeSidebar();
        });
        el.querySelector('.conv-item-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });
        convList.appendChild(el);
    });
}

async function createConversation() {
    try {
        const conv = await apiPost('/api/chat/conversations', {});
        conversations.unshift(conv);
        renderConversationList();
        selectConversation(conv.id);
        closeSidebar();
    } catch (err) {
        console.error('Error creating conversation:', err);
    }
}

async function selectConversation(id) {
    exitSelectionMode();
    currentConversationId = id;
    const conv = conversations.find(c => c.id === id);
    chatTitle.textContent = conv ? conv.title : 'Secretaria';
    welcomeMsg.hidden = true;
    inputBar.hidden = false;
    renderConversationList();
    clearPendingFile();

    // Load messages
    chatMessages.innerHTML = '';
    try {
        const messages = await apiGet(`/api/chat/conversations/${id}/messages`);
        messages.forEach(m => renderMessage(m.role, m.content, m.created_at, m.files, m.id));
        scrollToBottom();
    } catch (err) {
        console.error('Error loading messages:', err);
    }

    msgInput.focus();
}

async function deleteConversation(id) {
    if (!confirm('Eliminar esta conversacion?')) return;
    try {
        await apiDelete(`/api/chat/conversations/${id}`);
        conversations = conversations.filter(c => c.id !== id);
        renderConversationList();
        if (currentConversationId === id) {
            currentConversationId = null;
            chatMessages.innerHTML = '';
            welcomeMsg.hidden = false;
            chatMessages.appendChild(welcomeMsg);
            inputBar.hidden = true;
            chatTitle.textContent = 'Secretaria';
            clearPendingFile();
        }
    } catch (err) {
        console.error('Error deleting conversation:', err);
    }
}

// --- File Upload ---

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.txt', '.jpg', '.jpeg', '.png', '.webp'];
const MAX_UPLOAD_SIZE = 20 * 1024 * 1024; // 20 MB

btnAttach.addEventListener('click', () => {
    if (isUploading || isStreaming) return;
    fileInput.click();
});

fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    fileInput.value = ''; // reset so same file can be re-selected
    if (!file) return;

    // Validate extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
        alert('Tipo de archivo no permitido: ' + ext);
        return;
    }

    // Validate size
    if (file.size > MAX_UPLOAD_SIZE) {
        alert('Archivo demasiado grande (max 20 MB)');
        return;
    }

    // Show preview
    pendingFile = file;
    pendingFileId = null;
    attachmentPreviewName.textContent = file.name;
    attachmentPreviewSize.textContent = formatFileSize(file.size);
    attachmentPreview.hidden = false;

    // Upload in background
    await uploadFile(file);
});

btnRemoveAttachment.addEventListener('click', () => {
    clearPendingFile();
});

function clearPendingFile() {
    pendingFile = null;
    pendingFileId = null;
    isUploading = false;
    attachmentPreview.hidden = true;
    attachmentPreviewName.textContent = '';
    attachmentPreviewSize.textContent = '';
    btnAttach.disabled = false;
}

async function uploadFile(file) {
    if (!currentConversationId) return;

    isUploading = true;
    btnAttach.disabled = true;
    attachmentPreviewSize.textContent = 'Subiendo...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(
            API + `/api/upload/conversations/${currentConversationId}/files`,
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${getToken()}` },
                body: formData,
            }
        );

        if (res.status === 401) {
            clearAuth();
            showScreen('login');
            throw new Error('Sesion expirada');
        }

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error subiendo archivo');

        pendingFileId = data.id;
        attachmentPreviewSize.textContent = formatFileSize(file.size);
    } catch (err) {
        alert('Error subiendo archivo: ' + err.message);
        clearPendingFile();
    } finally {
        isUploading = false;
        btnAttach.disabled = false;
    }
}

// --- Telegram ---

function openTelegramModal() {
    telegramModal.classList.add('active');
    telegramOverlay.classList.add('active');
    renderTelegramContacts();
    checkBotStatus();
}

function closeTelegramModal() {
    telegramModal.classList.remove('active', 'picker-mode');
    telegramOverlay.classList.remove('active');
}

btnTelegram.addEventListener('click', openTelegramModal);
telegramOverlay.addEventListener('click', closeTelegramModal);
$('#btn-close-telegram').addEventListener('click', closeTelegramModal);

async function checkBotStatus() {
    try {
        const data = await apiGet('/api/telegram/bot-status');
        if (data.configured && data.bot) {
            telegramBotStatus.textContent = '@' + data.bot.username;
            telegramBotStatus.classList.add('online');
        } else {
            telegramBotStatus.textContent = 'No configurado';
            telegramBotStatus.classList.remove('online');
        }
    } catch {
        telegramBotStatus.textContent = 'Error';
        telegramBotStatus.classList.remove('online');
    }
}

async function loadTelegramContacts() {
    try {
        telegramContacts = await apiGet('/api/telegram/contacts');
    } catch {
        telegramContacts = [];
    }
}

function renderTelegramContacts() {
    telegramContactsList.innerHTML = '';
    if (telegramContacts.length === 0) {
        telegramContactsList.innerHTML = '<div class="forward-menu-empty">Sin contactos. Agrega uno abajo.</div>';
        return;
    }
    telegramContacts.forEach(c => {
        const el = document.createElement('div');
        el.className = 'telegram-contact-item';
        el.innerHTML = `
            <div class="telegram-contact-info">
                <div class="telegram-contact-name">${escapeHtml(c.name)}</div>
                <div class="telegram-contact-chatid">${escapeHtml(c.chat_id)}</div>
            </div>
            <button class="telegram-contact-delete" title="Eliminar">&times;</button>
        `;
        el.querySelector('.telegram-contact-delete').addEventListener('click', () => {
            deleteTelegramContact(c.id);
        });
        telegramContactsList.appendChild(el);
    });
}

telegramAddForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = $('#tg-name').value.trim();
    const chatId = $('#tg-chat-id').value.trim();
    if (!name || !chatId) return;
    await addTelegramContact(name, chatId);
    $('#tg-name').value = '';
    $('#tg-chat-id').value = '';
});

async function addTelegramContact(name, chatId) {
    try {
        const contact = await apiPost('/api/telegram/contacts', { name, chat_id: chatId });
        telegramContacts.unshift(contact);
        renderTelegramContacts();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function deleteTelegramContact(id) {
    if (!confirm('Eliminar contacto?')) return;
    try {
        await apiDelete(`/api/telegram/contacts/${id}`);
        telegramContacts = telegramContacts.filter(c => c.id !== id);
        renderTelegramContacts();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// --- Google ---

function openGoogleModal() {
    googleModal.classList.add('active');
    googleOverlay.classList.add('active');
    checkGoogleStatus();
}

function closeGoogleModal() {
    googleModal.classList.remove('active');
    googleOverlay.classList.remove('active');
}

btnGoogle.addEventListener('click', openGoogleModal);
googleOverlay.addEventListener('click', closeGoogleModal);
$('#btn-close-google').addEventListener('click', closeGoogleModal);

async function checkGoogleStatus() {
    try {
        const data = await apiGet('/api/google/status');
        googleConnected = data.connected;
        updateGoogleUI(data);
    } catch {
        googleConnected = false;
        updateGoogleUI({ connected: false, scopes: [] });
    }
}

const SCOPE_LABELS = {
    'https://www.googleapis.com/auth/calendar': 'Calendar',
    'https://www.googleapis.com/auth/gmail.modify': 'Gmail',
    'https://www.googleapis.com/auth/drive': 'Drive',
    'https://www.googleapis.com/auth/contacts.readonly': 'Contacts',
};

function updateGoogleUI(data) {
    btnGoogle.classList.toggle('connected', data.connected);
    if (data.connected) {
        googleDisconnected.hidden = true;
        googleConnectedSection.hidden = false;
        googleScopesList.innerHTML = '';
        (data.scopes || []).forEach(scope => {
            const label = SCOPE_LABELS[scope] || scope.split('/').pop();
            const el = document.createElement('span');
            el.className = 'google-scope-item';
            el.textContent = label;
            googleScopesList.appendChild(el);
        });
        loadCalendarEvents();
        loadGmailMessages();
    } else {
        googleDisconnected.hidden = false;
        googleConnectedSection.hidden = true;
    }
}

btnGoogleConnect.addEventListener('click', async () => {
    try {
        const data = await apiGet('/api/google/auth-url');
        window.location.href = data.auth_url;
    } catch (err) {
        showToast('Error: ' + err.message);
    }
});

btnGoogleDisconnect.addEventListener('click', async () => {
    if (!confirm('Desconectar tu cuenta de Google?')) return;
    try {
        await apiPost('/api/google/disconnect', {});
        googleConnected = false;
        updateGoogleUI({ connected: false, scopes: [] });
        showToast('Google desconectado');
    } catch (err) {
        showToast('Error: ' + err.message);
    }
});

// --- Google Calendar ---

let gcalPeriod = 'today';
const gcalEvents = $('#gcal-events');
const gcalForm = $('#gcal-form');
const btnGcalAdd = $('#btn-gcal-add');
const btnGcalCancel = $('#btn-gcal-cancel');
const btnGcalSave = $('#btn-gcal-save');
const gcalTabs = document.querySelectorAll('.gcal-tab');

gcalTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        gcalPeriod = tab.dataset.period;
        gcalTabs.forEach(t => t.classList.toggle('active', t.dataset.period === gcalPeriod));
        loadCalendarEvents();
    });
});

btnGcalAdd.addEventListener('click', () => {
    gcalForm.hidden = !gcalForm.hidden;
    if (!gcalForm.hidden) {
        // Pre-fill start/end with reasonable defaults
        const now = new Date();
        const start = new Date(now.getTime() + 60 * 60 * 1000); // +1h
        const end = new Date(start.getTime() + 60 * 60 * 1000); // +1h
        $('#gcal-start').value = toLocalISOString(start);
        $('#gcal-end').value = toLocalISOString(end);
        $('#gcal-summary').value = '';
        $('#gcal-location').value = '';
        $('#gcal-description').value = '';
        $('#gcal-summary').focus();
    }
});

btnGcalCancel.addEventListener('click', () => {
    gcalForm.hidden = true;
});

btnGcalSave.addEventListener('click', async () => {
    const summary = $('#gcal-summary').value.trim();
    const start = $('#gcal-start').value;
    const end = $('#gcal-end').value;
    if (!summary || !start || !end) {
        showToast('Completa titulo, inicio y fin');
        return;
    }
    btnGcalSave.disabled = true;
    try {
        // Convert local datetime-local to ISO with timezone offset
        const startISO = new Date(start).toISOString();
        const endISO = new Date(end).toISOString();
        await apiPost('/api/google/calendar/events', {
            summary,
            start: startISO,
            end: endISO,
            location: $('#gcal-location').value.trim() || null,
            description: $('#gcal-description').value.trim() || null,
        });
        gcalForm.hidden = true;
        showToast('Evento creado');
        loadCalendarEvents();
    } catch (err) {
        showToast('Error: ' + err.message);
    } finally {
        btnGcalSave.disabled = false;
    }
});

async function loadCalendarEvents() {
    if (!googleConnected) return;
    gcalEvents.innerHTML = '<div class="gcal-loading">Cargando...</div>';
    try {
        const endpoint = gcalPeriod === 'week'
            ? '/api/google/calendar/events/week'
            : '/api/google/calendar/events/today';
        const events = await apiGet(endpoint);
        renderCalendarEvents(events);
    } catch (err) {
        gcalEvents.innerHTML = '<div class="gcal-empty">Error cargando eventos</div>';
    }
}

function renderCalendarEvents(events) {
    gcalEvents.innerHTML = '';
    if (events.length === 0) {
        gcalEvents.innerHTML = '<div class="gcal-empty">Sin eventos</div>';
        return;
    }
    events.forEach(ev => {
        const el = document.createElement('div');
        el.className = 'gcal-event';
        const timeStr = formatCalendarTime(ev.start);
        const locationHtml = ev.location
            ? `<div class="gcal-event-location">${escapeHtml(ev.location)}</div>`
            : '';
        el.innerHTML = `
            <div class="gcal-event-time">${escapeHtml(timeStr)}</div>
            <div class="gcal-event-info">
                <div class="gcal-event-title">${escapeHtml(ev.summary)}</div>
                ${locationHtml}
            </div>
            <button class="gcal-event-delete" title="Eliminar">&times;</button>
        `;
        if (ev.html_link) {
            el.querySelector('.gcal-event-info').style.cursor = 'pointer';
            el.querySelector('.gcal-event-info').addEventListener('click', () => {
                window.open(ev.html_link, '_blank');
            });
        }
        el.querySelector('.gcal-event-delete').addEventListener('click', async () => {
            if (!confirm('Eliminar evento?')) return;
            try {
                await apiDelete(`/api/google/calendar/events/${ev.id}`);
                showToast('Evento eliminado');
                loadCalendarEvents();
            } catch (err) {
                showToast('Error: ' + err.message);
            }
        });
        gcalEvents.appendChild(el);
    });
}

function formatCalendarTime(isoStr) {
    if (!isoStr) return '';
    // Date-only events (all-day)
    if (isoStr.length === 10) return 'Todo el dia';
    const d = new Date(isoStr);
    return d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
}

function toLocalISOString(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d}T${h}:${min}`;
}

// --- Gmail ---

let gmailTab = 'inbox';
const gmailMessages = $('#gmail-messages');
const gmailCompose = $('#gmail-compose');
const gmailDetail = $('#gmail-detail');
const btnGmailCompose = $('#btn-gmail-compose');
const btnGmailCancel = $('#btn-gmail-cancel');
const btnGmailSend = $('#btn-gmail-send');
const btnGmailBack = $('#btn-gmail-back');
const gmailUnreadBadge = $('#gmail-unread-badge');
const gmailTabs = document.querySelectorAll('.gmail-tab');

gmailTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        gmailTab = tab.dataset.gmailTab;
        gmailTabs.forEach(t => t.classList.toggle('active', t.dataset.gmailTab === gmailTab));
        loadGmailMessages();
    });
});

btnGmailCompose.addEventListener('click', () => {
    gmailCompose.hidden = !gmailCompose.hidden;
    gmailDetail.hidden = true;
    if (!gmailCompose.hidden) {
        $('#gmail-to').value = '';
        $('#gmail-subject').value = '';
        $('#gmail-body').value = '';
        $('#gmail-to').focus();
    }
});

btnGmailCancel.addEventListener('click', () => {
    gmailCompose.hidden = true;
});

btnGmailSend.addEventListener('click', async () => {
    const to = $('#gmail-to').value.trim();
    const subject = $('#gmail-subject').value.trim();
    const body = $('#gmail-body').value.trim();
    if (!to) { showToast('Ingresa un destinatario'); return; }
    if (!body) { showToast('Escribe un mensaje'); return; }
    btnGmailSend.disabled = true;
    try {
        await apiPost('/api/google/gmail/send', { to, subject, body });
        gmailCompose.hidden = true;
        showToast('Correo enviado');
        loadGmailMessages();
    } catch (err) {
        showToast('Error: ' + err.message);
    } finally {
        btnGmailSend.disabled = false;
    }
});

btnGmailBack.addEventListener('click', () => {
    gmailDetail.hidden = true;
});

async function loadGmailMessages() {
    if (!googleConnected) return;
    gmailMessages.innerHTML = '<div class="gmail-loading">Cargando...</div>';
    gmailDetail.hidden = true;
    try {
        const endpoint = gmailTab === 'unread'
            ? '/api/google/gmail/messages/unread'
            : '/api/google/gmail/messages?max=20';
        const messages = await apiGet(endpoint);
        renderGmailMessages(messages);
        // Update unread badge
        if (gmailTab === 'inbox') {
            const unreadCount = messages.filter(m => m.unread).length;
            gmailUnreadBadge.textContent = unreadCount;
            gmailUnreadBadge.hidden = unreadCount === 0;
        }
    } catch (err) {
        gmailMessages.innerHTML = '<div class="gmail-empty">Error cargando correos</div>';
    }
}

function renderGmailMessages(messages) {
    gmailMessages.innerHTML = '';
    if (messages.length === 0) {
        gmailMessages.innerHTML = '<div class="gmail-empty">Sin correos</div>';
        return;
    }
    messages.forEach(msg => {
        const el = document.createElement('div');
        el.className = 'gmail-msg' + (msg.unread ? ' unread' : '');
        const dateStr = formatGmailDate(msg.date);
        const fromShort = msg.from.split('<')[0].trim() || msg.from;
        el.innerHTML = `
            <div class="gmail-msg-row">
                <div class="gmail-msg-from">${escapeHtml(fromShort)}</div>
                <div class="gmail-msg-date">${escapeHtml(dateStr)}</div>
            </div>
            <div class="gmail-msg-subject">${escapeHtml(msg.subject || '(Sin asunto)')}</div>
            <div class="gmail-msg-snippet">${escapeHtml(msg.snippet)}</div>
        `;
        el.addEventListener('click', () => openGmailDetail(msg.id));
        gmailMessages.appendChild(el);
    });
}

function formatGmailDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr);
        const now = new Date();
        if (d.toDateString() === now.toDateString()) {
            return d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
        }
        return d.toLocaleDateString('es', { day: 'numeric', month: 'short' });
    } catch {
        return dateStr;
    }
}

async function openGmailDetail(messageId) {
    gmailDetail.hidden = false;
    $('#gmail-detail-subject').textContent = 'Cargando...';
    $('#gmail-detail-meta').textContent = '';
    $('#gmail-detail-body').textContent = '';
    try {
        const msg = await apiGet(`/api/google/gmail/messages/${messageId}`);
        $('#gmail-detail-subject').textContent = msg.subject || '(Sin asunto)';
        $('#gmail-detail-meta').textContent = `De: ${msg.from}\nPara: ${msg.to}\nFecha: ${msg.date}`;
        $('#gmail-detail-body').textContent = msg.body || '(Sin contenido de texto)';
    } catch (err) {
        $('#gmail-detail-subject').textContent = 'Error';
        $('#gmail-detail-body').textContent = err.message;
    }
}

// --- Selection Mode ---

function enterSelectionMode(initialBubble) {
    if (selectionMode) return;
    selectionMode = true;
    selectedMessageIds.clear();
    document.body.classList.add('selection-mode');
    if (initialBubble && initialBubble.dataset.msgId) {
        toggleMessageSelection(initialBubble);
    }
}

function exitSelectionMode() {
    if (!selectionMode) return;
    selectionMode = false;
    selectedMessageIds.clear();
    document.body.classList.remove('selection-mode');
    chatMessages.querySelectorAll('.msg-bubble.selected').forEach(b => b.classList.remove('selected'));
    updateSelectionToolbar();
}

function toggleMessageSelection(bubble) {
    const msgId = bubble.dataset.msgId;
    if (!msgId) return;
    const id = parseInt(msgId);
    if (selectedMessageIds.has(id)) {
        selectedMessageIds.delete(id);
        bubble.classList.remove('selected');
    } else {
        selectedMessageIds.add(id);
        bubble.classList.add('selected');
    }
    updateSelectionToolbar();
}

function updateSelectionToolbar() {
    const count = selectedMessageIds.size;
    selectionCount.textContent = `${count} seleccionado${count !== 1 ? 's' : ''}`;
    btnSelectionForward.disabled = count === 0;
}

function showContactPicker() {
    telegramModal.classList.add('active', 'picker-mode');
    telegramOverlay.classList.add('active');
    renderContactPicker();
    checkBotStatus();
}

function closeContactPicker() {
    telegramModal.classList.remove('active', 'picker-mode');
    telegramOverlay.classList.remove('active');
}

function renderContactPicker() {
    telegramContactsList.innerHTML = '';
    if (telegramContacts.length === 0) {
        telegramContactsList.innerHTML = '<div class="forward-menu-empty">Sin contactos. Abre Telegram para agregar uno.</div>';
        return;
    }
    telegramContacts.forEach(c => {
        const el = document.createElement('div');
        el.className = 'telegram-contact-item';
        el.innerHTML = `
            <div class="telegram-contact-info">
                <div class="telegram-contact-name">${escapeHtml(c.name)}</div>
                <div class="telegram-contact-chatid">${escapeHtml(c.chat_id)}</div>
            </div>
        `;
        el.addEventListener('click', () => {
            closeContactPicker();
            forwardSelectedToTelegram(c.id, c.name);
        });
        telegramContactsList.appendChild(el);
    });
}

async function forwardSelectedToTelegram(contactId, contactName) {
    const ids = Array.from(selectedMessageIds);
    exitSelectionMode();

    showToast('Enviando...');
    try {
        const result = await apiPost('/api/telegram/send-bulk', {
            message_ids: ids,
            contact_id: contactId,
        });
        if (result.ok) {
            showToast(`Enviado a ${contactName}`);
        } else {
            showToast(result.detail || 'Error al enviar');
        }
    } catch (err) {
        showToast('Error: ' + err.message);
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toastContainer.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// Selection toolbar handlers
btnSelectionClose.addEventListener('click', exitSelectionMode);
btnSelectionForward.addEventListener('click', showContactPicker);

// Long-press / right-click for selection mode
let longPressTimer = null;
let longPressTriggered = false;

chatMessages.addEventListener('touchstart', (e) => {
    const bubble = e.target.closest('.msg-bubble[data-msg-id]');
    if (!bubble) return;
    longPressTriggered = false;
    longPressTimer = setTimeout(() => {
        longPressTriggered = true;
        e.preventDefault();
        if (!selectionMode) {
            enterSelectionMode(bubble);
        } else {
            toggleMessageSelection(bubble);
        }
    }, 500);
}, { passive: false });

chatMessages.addEventListener('touchend', () => {
    clearTimeout(longPressTimer);
});

chatMessages.addEventListener('touchmove', () => {
    clearTimeout(longPressTimer);
});

chatMessages.addEventListener('contextmenu', (e) => {
    const bubble = e.target.closest('.msg-bubble[data-msg-id]');
    if (!bubble) return;
    e.preventDefault();
    if (!selectionMode) {
        enterSelectionMode(bubble);
    } else {
        toggleMessageSelection(bubble);
    }
});

chatMessages.addEventListener('click', (e) => {
    if (!selectionMode) return;
    if (longPressTriggered) { longPressTriggered = false; return; }
    const bubble = e.target.closest('.msg-bubble[data-msg-id]');
    if (!bubble) return;
    e.preventDefault();
    e.stopPropagation();
    toggleMessageSelection(bubble);
});

// --- Messages ---

function stripThinkTags(text) {
    // Strip complete <think>...</think> blocks
    let result = text.replace(/<think>[\s\S]*?<\/think>/gi, '');
    // Strip incomplete <think> block (opening tag arrived, closing not yet — during streaming)
    result = result.replace(/<think>[\s\S]*$/gi, '');
    return result.trim();
}

function renderMessage(role, content, timestamp, files, messageId) {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${role}`;

    // Set data-msg-id on ALL messages (user and assistant) for selection
    if (messageId) {
        bubble.dataset.msgId = messageId;
    }

    // Render file attachments
    if (files && files.length > 0) {
        for (const f of files) {
            // Generated documents (assistant files with .docx from doc generation)
            if (role === 'assistant' && f.filename && f.filename.startsWith('doc_') && (f.filename.endsWith('.docx') || f.filename.endsWith('.txt'))) {
                bubble.appendChild(createDocCard(f));
            } else if (f.file_type === 'image') {
                const img = document.createElement('img');
                img.className = 'msg-file-image';
                img.src = authUrl(API + `/api/upload/files/${f.id}`);
                img.alt = f.filename;
                img.loading = 'lazy';
                img.addEventListener('click', () => {
                    if (selectionMode) return;
                    window.open(authUrl(API + `/api/upload/files/${f.id}`), '_blank');
                });
                bubble.appendChild(img);
            } else {
                const fileEl = document.createElement('a');
                fileEl.className = 'msg-file';
                fileEl.href = authUrl(API + `/api/upload/files/${f.id}`);
                fileEl.target = '_blank';
                fileEl.rel = 'noopener';
                fileEl.addEventListener('click', (e) => {
                    if (selectionMode) e.preventDefault();
                });

                const ext = f.filename.split('.').pop().toUpperCase();
                fileEl.innerHTML = `
                    <div class="file-icon">${escapeHtml(ext)}</div>
                    <div class="msg-file-info">
                        <div class="msg-file-name">${escapeHtml(f.filename)}</div>
                        <div class="msg-file-size">${formatFileSize(f.size_bytes)}</div>
                    </div>
                `;
                bubble.appendChild(fileEl);
            }
        }
    }

    // Render text content (skip placeholder if we have files)
    let displayContent = (files && files.length > 0 && content === '[Archivo adjunto]') ? '' : content;
    if (displayContent && role === 'assistant') {
        displayContent = stripThinkTags(displayContent);
    }
    if (displayContent) {
        const textEl = document.createElement('div');
        textEl.className = 'msg-text';
        textEl.textContent = displayContent;
        bubble.appendChild(textEl);
    }

    if (timestamp) {
        const timeEl = document.createElement('div');
        timeEl.className = 'msg-time';
        timeEl.textContent = formatTime(timestamp);
        bubble.appendChild(timeEl);
    }

    chatMessages.appendChild(bubble);
    return bubble;
}

function createDocCard(fileInfo) {
    const ext = fileInfo.filename.split('.').pop().toUpperCase();
    const card = document.createElement('a');
    card.className = 'msg-generated-doc';
    card.href = authUrl(API + `/api/documents/${fileInfo.id}`);
    card.target = '_blank';
    card.rel = 'noopener';
    card.innerHTML = `
        <div class="doc-icon">
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
        </div>
        <div class="doc-info">
            <div class="doc-name">${escapeHtml(fileInfo.filename)}</div>
            <div class="doc-meta">${ext}${fileInfo.size_bytes ? ' · ' + formatFileSize(fileInfo.size_bytes) : ''}</div>
        </div>
        <div class="doc-download">
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
        </div>
    `;
    return card;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    if (selectionMode) return;
    const content = msgInput.value.trim();
    const hasFile = pendingFileId !== null;

    if ((!content && !hasFile) || !currentConversationId || isStreaming || isUploading) return;

    isStreaming = true;
    btnSend.disabled = true;
    msgInput.value = '';
    autoResizeInput();

    // Capture file info before clearing
    const fileIds = hasFile ? [pendingFileId] : [];
    const fileForBubble = hasFile && pendingFile ? {
        id: pendingFileId,
        filename: pendingFile.name,
        file_type: isImageFile(pendingFile.name) ? 'image' : 'document',
        size_bytes: pendingFile.size,
    } : null;

    clearPendingFile();

    // Render user bubble with attachment (no messageId yet, will be set via SSE)
    const userFiles = fileForBubble ? [fileForBubble] : [];
    const userBubble = renderMessage('user', content || '[Archivo adjunto]', new Date().toISOString(), userFiles);
    scrollToBottom();

    // Show typing indicator
    typingIndicator.hidden = false;
    scrollToBottom();

    // Create assistant bubble for streaming
    const aiBubble = renderMessage('assistant', '', null, null);
    const textEl = aiBubble.querySelector('.msg-text');
    if (!textEl) {
        // Add text element since renderMessage skips empty content
        const newTextEl = document.createElement('div');
        newTextEl.className = 'msg-text';
        aiBubble.appendChild(newTextEl);
    }
    const streamTextEl = aiBubble.querySelector('.msg-text');
    aiBubble.style.display = 'none'; // hide until first chunk

    try {
        const body = { content, use_search: searchMode, generate_doc: docMode };
        if (docMode) body.doc_format = docFormatSelect.value;
        if (fileIds.length > 0) body.file_ids = fileIds;

        const res = await fetch(API + `/api/chat/conversations/${currentConversationId}/messages`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body),
        });

        if (res.status === 401) {
            clearAuth();
            showScreen('login');
            return;
        }

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Error del servidor');
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const data = line.slice(6);
                if (data === '[DONE]') continue;

                // Detect generated document event
                if (data.startsWith('[FILE:') && data.endsWith(']')) {
                    try {
                        const fileInfo = JSON.parse(data.slice(6, -1));
                        aiBubble.appendChild(createDocCard(fileInfo));
                        scrollToBottom();
                    } catch (e) { /* ignore parse error */ }
                    continue;
                }

                // Detect user message ID event
                const userMsgIdMatch = data.match(/^\[USER_MSG_ID:(\d+)\]$/);
                if (userMsgIdMatch) {
                    userBubble.dataset.msgId = userMsgIdMatch[1];
                    continue;
                }

                // Detect assistant message ID event
                const msgIdMatch = data.match(/^\[MSG_ID:(\d+)\]$/);
                if (msgIdMatch) {
                    aiBubble.dataset.msgId = msgIdMatch[1];
                    continue;
                }

                fullText += data.replaceAll('\\n', '\n');
                typingIndicator.hidden = true;
                aiBubble.style.display = '';
                streamTextEl.textContent = stripThinkTags(fullText);
                scrollToBottom();
            }
        }

        // Add timestamp to the AI bubble
        if (fullText) {
            const timeEl = document.createElement('div');
            timeEl.className = 'msg-time';
            timeEl.textContent = formatTime(new Date().toISOString());
            aiBubble.appendChild(timeEl);
        } else {
            aiBubble.remove();
        }

        // Update conversation title in sidebar if it changed
        await loadConversations();

        // Refresh file explorer if active
        if (activeTab === 'files') loadExplorerFiles();

    } catch (err) {
        typingIndicator.hidden = true;
        aiBubble.style.display = '';
        streamTextEl.textContent = 'Error: ' + err.message;
        aiBubble.classList.add('error');
    } finally {
        isStreaming = false;
        btnSend.disabled = false;
        typingIndicator.hidden = true;
        scrollToBottom();
        msgInput.focus();
    }
}

// --- Input handling ---

btnSend.addEventListener('click', sendMessage);

msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

msgInput.addEventListener('input', autoResizeInput);

function autoResizeInput() {
    msgInput.style.height = 'auto';
    msgInput.style.height = Math.min(msgInput.scrollHeight, 150) + 'px';
}

// --- New conversation ---
$('#btn-new-conv').addEventListener('click', createConversation);

// --- Logout ---
$('#btn-logout').addEventListener('click', () => {
    exitSelectionMode();
    clearAuth();
    currentConversationId = null;
    conversations = [];
    telegramContacts = [];
    explorerFiles = [];
    googleConnected = false;
    activeTab = 'conversations';
    clearPendingFile();
    closeTelegramModal();
    closeGoogleModal();
    btnGoogle.classList.remove('connected');
    // Reset sidebar to conversations tab
    sidebarTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === 'conversations'));
    convList.hidden = false;
    fileExplorer.hidden = true;
    sidebar.classList.remove('files-active');
    showScreen('login');
});

// --- Helpers ---

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoStr) {
    const d = new Date(isoStr);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) {
        return d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('es', { day: 'numeric', month: 'short' });
}

function formatTime(isoStr) {
    return new Date(isoStr).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
}

function formatFileSize(bytes) {
    if (bytes == null) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function isImageFile(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
}

// --- App Init ---

function enterApp() {
    showScreen('chat');
    welcomeMsg.hidden = false;
    chatMessages.innerHTML = '';
    chatMessages.appendChild(welcomeMsg);
    inputBar.hidden = true;
    chatTitle.textContent = 'Secretaria';
    currentConversationId = null;
    clearPendingFile();
    loadConversations();
    loadTelegramContacts();
    loadExplorerFiles();
    checkGoogleStatus();

    // Detect Google OAuth redirect params
    const params = new URLSearchParams(window.location.search);
    if (params.get('google_connected') === 'true') {
        showToast('Google conectado exitosamente');
        window.history.replaceState({}, '', window.location.pathname);
    } else if (params.get('google_error')) {
        showToast('Error conectando Google: ' + params.get('google_error'));
        window.history.replaceState({}, '', window.location.pathname);
    }
}

function init() {
    if (getToken()) {
        enterApp();
    } else {
        showScreen('login');
    }
}

// Register service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
}

init();
