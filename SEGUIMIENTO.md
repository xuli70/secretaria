# SEGUIMIENTO - Secretaria

> **Objetivo:** Aplicación web mobile-first de asistente personal (secretaria) con chat continuo, gestión documental, generación de documentos y reenvío por Telegram
> **Carpeta:** D:\MINIMAX\Secretaria
> **Ultima actualizacion:** 2026-02-06
> **Estado global:** Fase 2 de 6 (completada)

---

## Resumen ejecutivo

Proyecto nuevo. Se ha definido la arquitectura, el stack técnico y las 7 fases de desarrollo. El cerebro es MINIMAX AI (chat) + Perplexity (búsqueda externa). La interfaz es un chat oscuro tipo WhatsApp optimizado para teléfono (PWA). Backend en Python/FastAPI, SQLite como BD, Docker para contenedores, Coolify para despliegue final desde GitHub.

**PROXIMO PASO:** Iniciar Fase 3: Perplexity + Busqueda Externa.

---

## Bloqueos activos

> **Sin bloqueos activos**

---

## Decisiones de diseño tomadas

| Decision | Resultado | Fecha |
|----------|-----------|-------|
| Autenticación | Login completo (usuario + contraseña, JWT) | 2026-02-06 |
| Estilo UI | Tema oscuro tipo WhatsApp, burbujas de chat | 2026-02-06 |
| Streaming AI | SSE (Server-Sent Events) para respuestas en tiempo real | 2026-02-06 |
| Modelo AI | MINIMAX MiniMax-M2 via API OpenAI-compatible | 2026-02-06 |
| API Keys | En variables de entorno Coolify, inyectadas al redeploy desde GitHub | 2026-02-06 |
| Despliegue | Desarrollo local Docker primero → Coolify cuando esté listo | 2026-02-06 |
| Stack backend | Python 3.11 + FastAPI + SQLAlchemy + SQLite | 2026-02-06 |
| Stack frontend | HTML/CSS/JS vanilla, PWA (manifest + service worker) | 2026-02-06 |
| Archivos upload | Un archivo por mensaje, max 20MB, sin OCR | 2026-02-06 |
| Tipos soportados | PDF, DOCX, XLSX, TXT (documentos) + JPG, JPEG, PNG, WEBP (imagenes) | 2026-02-06 |
| Extraccion texto | pypdf (PDF), python-docx (DOCX), openpyxl (XLSX), plain read (TXT) | 2026-02-06 |

---

## Fase 0: Estructura base + Autenticacion

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Crear estructura de carpetas (backend/, frontend/, data/)
- [x] Crear Dockerfile (Python 3.11, FastAPI)
- [x] Crear docker-compose.yml (puerto 8000, volumen /data)
- [x] Crear requirements.txt
- [x] Crear .env.example con todas las variables necesarias
- [x] Crear .gitignore
- [x] Implementar config.py (lectura de variables de entorno)
- [x] Implementar database.py (SQLAlchemy + SQLite, creacion de tablas)
- [x] Implementar models.py (todos los modelos ORM)
- [x] Implementar auth.py (JWT create/verify, hash/verify password)
- [x] Implementar backend/routers/auth.py (POST /register, POST /login)
- [x] Implementar main.py (FastAPI app, CORS, static files, /health)
- [x] Crear frontend/index.html con pantalla de login (dark theme)
- [x] Crear frontend/css/style.css (base oscura, mobile-first)
- [x] Crear frontend/js/app.js (gestion auth, token JWT en localStorage)
- [x] Crear frontend/manifest.json + sw.js (PWA basico)
- [x] Inicializar repo Git
- [x] Verificar docker compose up

### Verificacion
- [x] `docker compose up` arranca sin errores
- [x] GET /health → 200 OK
- [x] POST /api/auth/register crea usuario
- [x] POST /api/auth/login devuelve JWT
- [ ] Abrir en navegador movil → pantalla de login dark theme

---

## Fase 1: Chat Central + MINIMAX AI

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Crear backend/services/minimax_ai.py (cliente SSE streaming con httpx)
- [x] Crear backend/routers/chat.py (CRUD conversaciones + POST mensaje con streaming)
- [x] System prompt: "Eres Secretaria, un asistente personal eficiente y amable"
- [x] Historial de mensajes enviado a la IA (ultimos 50 mensajes)
- [x] Auto-titulo de conversacion con los primeros 50 chars del primer mensaje
- [x] Registrar chat router en main.py
- [x] Frontend: sidebar con lista de conversaciones (crear, seleccionar, eliminar)
- [x] Frontend: burbujas de chat (user verde, assistant oscuro) con timestamps
- [x] Frontend: streaming SSE en tiempo real (lectura chunk por chunk)
- [x] Frontend: indicador de escritura (typing dots animados)
- [x] Frontend: auto-resize del textarea de input
- [x] Frontend: boton hamburguesa para sidebar en movil

### Verificacion
- [x] Crear conversacion → aparece en sidebar
- [x] Enviar mensaje → burbuja user + respuesta AI en streaming
- [x] Historial persistente → recargar pagina mantiene mensajes
- [x] Eliminar conversacion funciona
- [x] Auto-titulo se aplica al primer mensaje

### Archivos creados/modificados
- `backend/routers/chat.py` — CRUD conversaciones + endpoint mensajes SSE
- `backend/services/minimax_ai.py` — Cliente streaming MINIMAX AI
- `backend/main.py` — Agregado chat_router
- `frontend/index.html` — Pantalla chat completa (sidebar, burbujas, input bar)
- `frontend/js/app.js` — Logica chat, streaming, conversaciones
- `frontend/css/style.css` — Estilos burbujas, sidebar, typing indicator

---

## Fase 2: Entrada Multimodal + Almacen

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Agregar pypdf y python-docx a requirements.txt
- [x] Agregar constantes de upload en backend/config.py (MAX_UPLOAD_SIZE, extensiones, MIME types)
- [x] Crear backend/services/file_handler.py (sanitize, classify, validate, save, extract_text)
- [x] Crear backend/routers/upload.py (POST upload, GET serve file, GET list files)
- [x] Modificar backend/routers/chat.py (schemas con files, file_ids en MessageCreate, inyeccion de texto extraido al AI, joinedload, delete con cleanup de disco)
- [x] Registrar upload_router en backend/main.py
- [x] Frontend: boton clip (paperclip SVG), input file oculto, area de preview de adjunto
- [x] Frontend: estilos para attach button, attachment preview, msg-file, msg-file-image, file-icon
- [x] Frontend: logica de upload (pendingFile, pendingFileId, isUploading), validacion client-side
- [x] Frontend: renderMessage con soporte de files (imagenes inline, cards de documentos)
- [x] Frontend: sendMessage con file_ids, permite enviar solo archivo sin texto
- [x] Frontend: formatFileSize helper, isImageFile helper

### Verificacion
- [x] Docker build exitoso con pypdf y python-docx instalados
- [x] FastAPI arranca sin errores de importacion (upload_router, file_handler)
- [x] GET /health → 200 OK con todos los routers registrados
- [ ] Subir PDF → texto extraido, archivo en /data/documentos/
- [ ] Subir imagen JPG → archivo en /data/imagenes/, sin texto extraido
- [ ] Subir .exe → error 400
- [ ] Subir archivo >20MB → error 400
- [ ] Enviar mensaje con adjunto → burbuja muestra archivo + texto
- [ ] Enviar solo archivo sin texto → funciona con placeholder
- [ ] IA recibe contexto del documento y responde sobre el contenido
- [ ] Click en imagen → abre en nueva pestaña
- [ ] Click en documento → descarga
- [ ] Recargar pagina → historial muestra adjuntos correctamente
- [ ] Eliminar conversacion → archivos borrados de disco

### Archivos creados/modificados
- `backend/services/file_handler.py` — CREADO: servicio de archivos (sanitize, classify, validate, save, extract_text para PDF/DOCX/XLSX/TXT)
- `backend/routers/upload.py` — CREADO: router de upload (POST subir, GET servir, GET listar)
- `backend/config.py` — Agregadas constantes de upload (MAX_UPLOAD_SIZE, extensiones, MIME types)
- `backend/routers/chat.py` — Schemas FileAttachment/MessageOut con files, MessageCreate con file_ids, inyeccion de texto extraido al contexto AI, joinedload en get_messages, delete con limpieza de archivos de disco
- `backend/main.py` — Registrado upload_router
- `requirements.txt` — Agregados pypdf y python-docx
- `frontend/index.html` — Boton clip, input file oculto, area preview de adjunto
- `frontend/css/style.css` — Estilos btn-attach, attachment-preview, msg-file, msg-file-image, file-icon
- `frontend/js/app.js` — Logica completa de upload, renderMessage con files, sendMessage con file_ids, helpers formatFileSize/isImageFile

---

## Fase 3: Perplexity + Busqueda Externa

> **Estado:** [ ] Pendiente
> **Prioridad:** Alta

---

## Fase 4: Generador de Documentos

> **Estado:** [ ] Pendiente
> **Prioridad:** Alta

---

## Fase 5: Telegram

> **Estado:** [ ] Pendiente
> **Prioridad:** Media

---

## Fase 6: Deploy Coolify

> **Estado:** [ ] Pendiente
> **Prioridad:** Media

---

## Notas de proceso

> **IMPORTANTE:** Este documento DEBE actualizarse al final de cada fase completada. Incluir: tareas realizadas, archivos creados/modificados, verificaciones y siguiente paso.

---

## Registro de sesiones

| Sesion | Fecha | Fase trabajada | Avances | Siguiente paso |
|--------|-------|----------------|---------|----------------|
| 1 | 2026-02-06 | Planificacion | Definido objetivo, arquitectura, stack, 7 fases | Iniciar Fase 0: scaffolding |
| 2 | 2026-02-06 | Fase 0 | Fase 0 completada: scaffolding, auth, Docker verificado, Git init | Iniciar Fase 1: Chat + MINIMAX AI |
| 3 | 2026-02-06 | Fase 1 | Fase 1 completada: chat router, minimax_ai service SSE, frontend burbujas+sidebar+streaming | Iniciar Fase 2: Entrada multimodal + almacen |
| 4 | 2026-02-06 | Fase 2 | Fase 2 completada: file_handler service, upload router, chat.py con files, frontend clip+preview+upload | Iniciar Fase 3: Perplexity + busqueda externa |
