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
const btnRegister = $('#btn-register');
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
    btnRegister.disabled = true;

    try {
        const data = await apiPost(endpoint, { username, password });
        saveAuth(data);
        enterApp();
    } catch (err) {
        showError(err.message);
    } finally {
        btnLogin.disabled = false;
        btnRegister.disabled = false;
    }
}

form.addEventListener('submit', (e) => {
    e.preventDefault();
    handleAuth('/api/auth/login');
});

btnRegister.addEventListener('click', () => {
    handleAuth('/api/auth/register');
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

// --- Search toggle ---

btnSearchToggle.addEventListener('click', () => {
    searchMode = !searchMode;
    if (searchMode) { docMode = false; btnDocToggle.classList.remove('active'); }
    btnSearchToggle.classList.toggle('active', searchMode);
    updateInputPlaceholder();
});

btnDocToggle.addEventListener('click', () => {
    docMode = !docMode;
    if (docMode) { searchMode = false; btnSearchToggle.classList.remove('active'); }
    btnDocToggle.classList.toggle('active', docMode);
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
        messages.forEach(m => renderMessage(m.role, m.content, m.created_at, m.files));
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

// --- Messages ---

function renderMessage(role, content, timestamp, files) {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${role}`;

    // Render file attachments
    if (files && files.length > 0) {
        for (const f of files) {
            // Generated documents (assistant files with .docx from doc generation)
            if (role === 'assistant' && f.filename && f.filename.startsWith('doc_') && f.filename.endsWith('.docx')) {
                bubble.appendChild(createDocCard(f));
            } else if (f.file_type === 'image') {
                const img = document.createElement('img');
                img.className = 'msg-file-image';
                img.src = API + `/api/upload/files/${f.id}`;
                img.alt = f.filename;
                img.loading = 'lazy';
                img.addEventListener('click', () => {
                    window.open(API + `/api/upload/files/${f.id}`, '_blank');
                });
                bubble.appendChild(img);
            } else {
                const fileEl = document.createElement('a');
                fileEl.className = 'msg-file';
                fileEl.href = API + `/api/upload/files/${f.id}`;
                fileEl.target = '_blank';
                fileEl.rel = 'noopener';

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
    const displayContent = (files && files.length > 0 && content === '[Archivo adjunto]') ? '' : content;
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
    const card = document.createElement('a');
    card.className = 'msg-generated-doc';
    card.href = API + `/api/documents/${fileInfo.id}`;
    card.target = '_blank';
    card.rel = 'noopener';
    card.innerHTML = `
        <div class="doc-icon">
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
        </div>
        <div class="doc-info">
            <div class="doc-name">${escapeHtml(fileInfo.filename)}</div>
            <div class="doc-meta">DOCX${fileInfo.size_bytes ? ' · ' + formatFileSize(fileInfo.size_bytes) : ''}</div>
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

    // Render user bubble with attachment
    const userFiles = fileForBubble ? [fileForBubble] : [];
    renderMessage('user', content || '[Archivo adjunto]', new Date().toISOString(), userFiles);
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

                fullText += data;
                typingIndicator.hidden = true;
                aiBubble.style.display = '';
                streamTextEl.textContent = fullText;
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
    msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + 'px';
}

// --- New conversation ---
$('#btn-new-conv').addEventListener('click', createConversation);

// --- Logout ---
$('#btn-logout').addEventListener('click', () => {
    clearAuth();
    currentConversationId = null;
    conversations = [];
    clearPendingFile();
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
