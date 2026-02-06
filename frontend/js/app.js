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

// --- Auth ---

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

async function apiPost(path, body) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(API + path, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });

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

// --- Logout ---

$('#btn-logout').addEventListener('click', () => {
    clearAuth();
    showScreen('login');
});

// --- App Init ---

function enterApp() {
    showScreen('chat');
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
