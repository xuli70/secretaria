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

    // Load messages
    chatMessages.innerHTML = '';
    try {
        const messages = await apiGet(`/api/chat/conversations/${id}/messages`);
        messages.forEach(m => renderMessage(m.role, m.content, m.created_at));
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
        }
    } catch (err) {
        console.error('Error deleting conversation:', err);
    }
}

// --- Messages ---

function renderMessage(role, content, timestamp) {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${role}`;

    const textEl = document.createElement('div');
    textEl.className = 'msg-text';
    textEl.textContent = content;
    bubble.appendChild(textEl);

    if (timestamp) {
        const timeEl = document.createElement('div');
        timeEl.className = 'msg-time';
        timeEl.textContent = formatTime(timestamp);
        bubble.appendChild(timeEl);
    }

    chatMessages.appendChild(bubble);
    return bubble;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const content = msgInput.value.trim();
    if (!content || !currentConversationId || isStreaming) return;

    isStreaming = true;
    btnSend.disabled = true;
    msgInput.value = '';
    autoResizeInput();

    // Render user bubble
    renderMessage('user', content, new Date().toISOString());
    scrollToBottom();

    // Show typing indicator
    typingIndicator.hidden = false;
    scrollToBottom();

    // Create assistant bubble for streaming
    const aiBubble = renderMessage('assistant', '', null);
    const textEl = aiBubble.querySelector('.msg-text');
    aiBubble.style.display = 'none'; // hide until first chunk

    try {
        const res = await fetch(API + `/api/chat/conversations/${currentConversationId}/messages`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ content }),
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

                fullText += data;
                typingIndicator.hidden = true;
                aiBubble.style.display = '';
                textEl.textContent = fullText;
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
        textEl.textContent = 'Error: ' + err.message;
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

// --- App Init ---

function enterApp() {
    showScreen('chat');
    welcomeMsg.hidden = false;
    chatMessages.innerHTML = '';
    chatMessages.appendChild(welcomeMsg);
    inputBar.hidden = true;
    chatTitle.textContent = 'Secretaria';
    currentConversationId = null;
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
