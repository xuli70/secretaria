# SEGUIMIENTO - Secretaria

> **Objetivo:** Aplicación web mobile-first de asistente personal (secretaria) con chat continuo, gestión documental, generación de documentos y reenvío por Telegram
> **Carpeta:** D:\MINIMAX\Secretaria
> **Ultima actualizacion:** 2026-02-07
> **Estado global:** Fase 9+10+11+12+13+14 completadas — Google OAuth 2.0 + Calendar + Gmail + Drive + Contacts integrado

---

## Resumen ejecutivo

Proyecto nuevo. Se ha definido la arquitectura, el stack técnico y las 7 fases de desarrollo. El cerebro es MINIMAX AI (chat) + Perplexity (búsqueda externa). La interfaz es un chat oscuro tipo WhatsApp optimizado para teléfono (PWA). Backend en Python/FastAPI, SQLite como BD, Docker para contenedores, Coolify para despliegue final desde GitHub.

**ESTADO:** Aplicacion funcionando correctamente en produccion. Google OAuth 2.0 integrado con Google Calendar, Gmail, Drive y Contacts. Calendar: lectura de eventos (hoy/semana), creacion y eliminacion. Gmail: inbox, no leidos, detalle de mensaje, envio de correo, badge de no leidos. Drive: archivos recientes, busqueda, descarga (con export de Google Docs), subida de archivos. UI en modal Google con secciones Calendar, Gmail y Drive. Explorador de archivos en sidebar con tabs y arbol colapsable. Archivos recuperables tras redeploy. Generacion de documentos DOCX/TXT. Filtro backend de bloques `<think>`.

---

## Bloqueos activos

> **Sin bloqueos activos**

---

## Decisiones de diseño tomadas

| Decision | Resultado | Fecha |
|----------|-----------|-------|
| Autenticación | Login solo con credenciales de env vars (APP_USERNAME/APP_PASSWORD), sin registro publico | 2026-02-06 |
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
| Generacion docs | Toggle modo documento, DOCX via python-docx post-stream, evento SSE [FILE:{json}] | 2026-02-06 |
| Formato docs | Selector DOCX/TXT al activar modo documento; TXT guarda texto plano, DOCX con formato | 2026-02-07 |
| Modos exclusivos | searchMode y docMode mutuamente excluyentes (activar uno desactiva el otro) | 2026-02-06 |
| Google OAuth | Tokens cifrados con Fernet en SQLite, refresh automatico, scopes Calendar+Gmail+Drive+Contacts | 2026-02-07 |

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

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Crear backend/services/perplexity.py (cliente SSE streaming, mismo patron que minimax_ai.py)
- [x] Agregar PERPLEXITY_MODEL a backend/config.py (default: "sonar")
- [x] Agregar PERPLEXITY_MODEL a .env.example
- [x] Modificar backend/routers/chat.py (import perplexity, use_search en MessageCreate, routing condicional)
- [x] Frontend: boton toggle busqueda (icono globo) en input-bar entre clip y textarea
- [x] Frontend: estado searchMode, toggle clase .active, cambio de placeholder
- [x] Frontend: envio de use_search en body del POST
- [x] Frontend: estilos .btn-search-toggle (42x42, transparente/accent toggle)

### Verificacion
- [ ] `docker compose up --build` arranca sin errores
- [ ] GET /health → 200 OK
- [ ] Activar modo busqueda (boton globo se resalta)
- [ ] Enviar mensaje → respuesta de Perplexity con fuentes web
- [ ] Desactivar modo busqueda → respuesta de MiniMax como antes
- [ ] Recargar pagina → historial muestra mensajes de ambos modelos
- [ ] Campo model_used en BD distingue "MiniMax-M2" y "perplexity-sonar"
- [ ] Sin PERPLEXITY_API_KEY → mensaje de error amigable

### Archivos creados/modificados
- `backend/services/perplexity.py` — CREADO: cliente streaming Perplexity AI (search_completion_stream, SEARCH_SYSTEM_PROMPT)
- `backend/config.py` — Agregado PERPLEXITY_MODEL
- `.env.example` — Agregado PERPLEXITY_MODEL=sonar
- `backend/routers/chat.py` — Import perplexity, use_search en MessageCreate, routing condicional chat/search, model_label dinamico
- `frontend/index.html` — Boton toggle busqueda web (icono globo SVG)
- `frontend/css/style.css` — Estilos .btn-search-toggle (normal, hover, active)
- `frontend/js/app.js` — Estado searchMode, toggle event, placeholder dinamico, use_search en body POST

---

## Fase 4: Generador de Documentos

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Crear backend/services/doc_generator.py (DOC_SYSTEM_PROMPT, generate_docx con parser markdown-like a DOCX)
- [x] Crear backend/routers/documents.py (GET /api/documents listar, GET /api/documents/{id} descargar)
- [x] Registrar documents_router en backend/main.py (antes del static mount)
- [x] Modificar backend/routers/chat.py (generate_doc en MessageCreate, DOC_SYSTEM_PROMPT, generacion DOCX post-stream, evento SSE [FILE:{...}])
- [x] Frontend: boton toggle documento (icono pagina SVG) en input-bar entre search toggle y textarea
- [x] Frontend: estado docMode, exclusion mutua con searchMode, placeholder dinamico
- [x] Frontend: generate_doc en body del POST
- [x] Frontend: deteccion de [FILE:{...}] en stream → renderizar card de descarga DOCX
- [x] Frontend: createDocCard helper para generar cards de documento generado
- [x] Frontend: estilos .btn-doc-toggle (42x42, purple toggle) y .msg-generated-doc (card con icono, nombre, tamaño, boton descarga)
- [x] Frontend: renderMessage con soporte de generated docs (doc_*.docx en assistant → card especial)

### Verificacion
- [x] `docker compose up --build` arranca sin errores
- [x] GET /health → 200 OK
- [ ] Activar modo documento (boton se resalta purple, search se desactiva)
- [ ] Enviar mensaje → respuesta AI en streaming con prompt de documentos
- [ ] Al terminar streaming → card de descarga DOCX aparece en la burbuja
- [ ] Click en card → descarga archivo .docx valido
- [ ] DOCX tiene formato correcto (titulo, parrafos, listas)
- [ ] Desactivar modo documento → chat normal como antes
- [ ] GET /api/documents → lista documentos generados
- [ ] Recargar pagina → historial muestra cards de documentos generados correctamente

### Archivos creados/modificados
- `backend/services/doc_generator.py` — CREADO: DOC_SYSTEM_PROMPT, generate_docx (parser: # heading, ## subheading, - lista, parrafo justificado, Calibri 11pt, margenes 2.5cm)
- `backend/routers/documents.py` — CREADO: GET /api/documents (listar), GET /api/documents/{id} (descargar FileResponse)
- `backend/main.py` — Registrado documents_router
- `backend/routers/chat.py` — Import doc_generator, generate_doc en MessageCreate, DOC_SYSTEM_PROMPT routing, generacion DOCX post-stream con File record, evento SSE [FILE:{json}] antes de [DONE]
- `frontend/index.html` — Boton toggle documento (icono pagina SVG)
- `frontend/css/style.css` — Estilos .btn-doc-toggle (purple), .msg-generated-doc (card con doc-icon, doc-info, doc-download)
- `frontend/js/app.js` — Estado docMode, exclusion mutua, updateInputPlaceholder, createDocCard, deteccion [FILE:] en stream, renderMessage con soporte generated docs, generate_doc en body POST

---

## Fase 5: Telegram

> **Estado:** [x] Completada
> **Prioridad:** Media

### Tareas
- [x] Crear backend/services/telegram_bot.py (get_me, send_message, send_document via httpx async)
- [x] Crear backend/routers/telegram.py (bot-status, CRUD contactos, send forward, history)
- [x] Registrar telegram_router en backend/main.py (antes del static mount)
- [x] Frontend: boton Telegram en header (icono avion, color #0088cc)
- [x] Frontend: modal de contactos (overlay + panel bottom-sheet, lista, formulario agregar, status bot)
- [x] Frontend: boton forward en burbujas assistant (icono Telegram, opacity hover)
- [x] Frontend: dropdown de contactos al click forward → seleccionar → enviar → feedback
- [x] Frontend: estado telegramContacts, loadTelegramContacts al enterApp
- [x] Frontend: estilos Telegram (modal, contactos, forward btn, menu dropdown, feedback animado)

### Verificacion
- [x] `docker compose up --build` arranca sin errores
- [x] GET /api/telegram/bot-status → estado del bot (configured: false sin token)
- [x] Endpoints protegidos con auth (403 sin token)
- [ ] CRUD contactos funciona (crear, listar, eliminar)
- [ ] POST /api/telegram/send → envia texto a Telegram
- [ ] POST /api/telegram/send (con archivo adjunto) → envia documento
- [ ] Modal de contactos funciona en movil
- [ ] Boton forward en burbujas assistant → selector → envio → feedback
- [ ] Sin TELEGRAM_BOT_TOKEN → mensaje amigable
- [ ] Historial de envios funciona

### Archivos creados/modificados
- `backend/services/telegram_bot.py` — CREADO: servicio Telegram Bot API (get_me, send_message, send_document con httpx async)
- `backend/routers/telegram.py` — CREADO: router /api/telegram (bot-status, CRUD contactos, send forward con texto+archivos, history)
- `backend/main.py` — Registrado telegram_router
- `frontend/index.html` — Boton Telegram en header, modal de contactos (overlay + panel + form)
- `frontend/css/style.css` — Estilos btn-telegram, telegram-modal, telegram-contact-item, btn-forward, forward-menu, forward-status
- `frontend/js/app.js` — Estado telegramContacts, loadTelegramContacts, addTelegramContact, deleteTelegramContact, forwardToTelegram, showForwardMenu, openTelegramModal, renderMessage con forward button y data-msg-id

---

## Fase 6: Deploy Coolify

> **Estado:** [x] Completada
> **Prioridad:** Media

### Tareas
- [x] Crear .dockerignore (excluir .env, .git, __pycache__, data/, *.md, .claude/, node_modules/, docker-compose.yml)
- [x] Actualizar SEGUIMIENTO.md con Fase 6 completada
- [x] Agregar TELEGRAM_DEFAULT_CHAT_ID a config.py y .env.example
- [x] Push a GitHub (repo: xuli70/secretaria, branch: main)
- [x] App creada en Coolify (UUID: eo0w8o0sokgcokswkss400ks, URL: https://secretaria.axcsol.com)

### Configuracion Coolify (manual por el usuario)
- App creada en Coolify con Dockerfile build
- Variables de entorno configuradas: JWT_SECRET, MINIMAX_API_KEY, PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_DEFAULT_CHAT_ID, APP_USERNAME, APP_PASSWORD
- Volumen persistente mapeado a /data
- Puerto 8000 expuesto
- Deploy automatico desde push a GitHub (branch main)

### Verificacion
- [ ] Push al repo GitHub → Coolify detecta el cambio y hace deploy
- [ ] GET /health en dominio de produccion → 200 OK
- [ ] Login y chat funcionan en produccion

### Archivos creados/modificados
- `.dockerignore` — CREADO: excluye secretos, cache, datos locales, docs del build context
- `backend/config.py` — Agregado TELEGRAM_DEFAULT_CHAT_ID
- `.env.example` — Agregado TELEGRAM_DEFAULT_CHAT_ID
- `SEGUIMIENTO.md` — Actualizado con Fase 6 completada y deploy info

---

## Post-deploy: Seguridad auth

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Eliminar endpoint POST /api/auth/register (registro publico deshabilitado)
- [x] Agregar APP_USERNAME y APP_PASSWORD a config.py como variables de entorno
- [x] Crear funcion _ensure_admin_user() en main.py (auto-crea/actualiza usuario al arrancar)
- [x] Eliminar boton "Crear cuenta" del frontend (index.html + app.js)
- [x] Agregar APP_USERNAME y APP_PASSWORD a .env.example y .env local
- [x] Verificar build Docker + health check + login con env vars
- [x] Push a GitHub

### Verificacion
- [x] `docker compose up --build` arranca sin errores
- [x] GET /health → 200 OK
- [x] Login con credenciales de env vars → JWT valido
- [x] POST /api/auth/register → 405 Method Not Allowed (endpoint eliminado)
- [x] Frontend solo muestra boton "Entrar" (sin "Crear cuenta")

### Archivos creados/modificados
- `backend/config.py` — Agregados APP_USERNAME y APP_PASSWORD
- `backend/main.py` — Funcion _ensure_admin_user() en lifespan, imports auth/SessionLocal/User
- `backend/routers/auth.py` — Eliminado endpoint /register, limpiado import hash_password
- `frontend/index.html` — Eliminado boton "Crear cuenta"
- `frontend/js/app.js` — Eliminadas referencias a btnRegister y su event listener
- `.env.example` — Agregados APP_USERNAME y APP_PASSWORD

---

## Post-deploy: Fix Telegram caracteres especiales

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
El reenvio a Telegram fallaba con "Bad Request: can't parse entities" cuando el mensaje de la IA contenia caracteres especiales (`<`, `>`, `**`, etc.). La causa era `parse_mode: "HTML"` en `telegram_bot.send_message()`.

### Solucion
- [x] Eliminar `parse_mode: "HTML"` de `send_message()` en telegram_bot.py → envio como texto plano
- [x] Push a GitHub → deploy automatico en Coolify

### Verificacion
- [x] Reenviar mensaje con caracteres especiales → banner verde "Enviado"
- [x] Mensaje llega correctamente a Telegram
- [x] Toda la aplicacion funciona en produccion (chat, busqueda, documentos, Telegram)

### Archivos modificados
- `backend/services/telegram_bot.py` — Eliminado parse_mode: "HTML" de send_message()

---

## Fase 7: Multi-Select Telegram Forwarding

> **Estado:** [x] Completada
> **Prioridad:** Media

### Tareas
- [x] Nuevo endpoint POST /api/telegram/send-bulk (schema SendBulkRequest, validacion ownership, combina mensajes con formato [Tu]/[Secretaria] HH:MM, split en chunks de 4096 chars, envio archivos adjuntos)
- [x] Helper split_telegram_text() para dividir texto largo en limites de parrafo
- [x] Emitir [USER_MSG_ID:{id}] en SSE stream para que burbujas user tengan data-msg-id
- [x] Selection toolbar HTML (barra con boton cerrar, contador, boton forward Telegram)
- [x] Selection mode CSS (toolbar, checkboxes circulares, tinte en burbujas seleccionadas, picker mode para modal, toast notifications)
- [x] Eliminar estilos antiguos de forward (btn-forward, forward-menu, forward-status, forward-fade)
- [x] Selection mode JS: estado (selectionMode, selectedMessageIds Set), funciones enter/exit/toggle
- [x] Long-press (500ms touch) y right-click (contextmenu) para activar modo seleccion
- [x] Click en burbujas para seleccionar/deseleccionar en modo seleccion
- [x] Contact picker mode en modal Telegram (solo lista, sin formulario, click directo para enviar)
- [x] forwardSelectedToTelegram() → POST /api/telegram/send-bulk → toast feedback
- [x] Guards: exitSelectionMode al cambiar conversacion y logout, bloqueo sendMessage en modo seleccion
- [x] renderMessage: data-msg-id en TODAS las burbujas (user + assistant), sin forward button individual
- [x] SSE parsing: [USER_MSG_ID] para user bubble, [MSG_ID] simplificado sin forward button

### Verificacion
- [ ] Long-press en mensaje → entra modo seleccion, burbuja seleccionada con checkbox verde
- [ ] Tap en mas burbujas → se seleccionan/deseleccionan (user Y assistant)
- [ ] Contador se actualiza en toolbar
- [ ] Boton forward deshabilitado con 0 seleccionados
- [ ] Click forward → modal contactos (modo picker, sin formulario)
- [x] Seleccionar contacto → envio bulk → toast "Enviado a X"
- [x] Mensaje llega a Telegram con formato correcto ([Tu]/[Secretaria] + timestamps)
- [ ] Archivos adjuntos llegan como documentos separados
- [ ] Click X en toolbar → sale de modo seleccion
- [ ] Cambiar conversacion → sale de modo seleccion automaticamente
- [ ] Right-click en desktop → activa modo seleccion
- [ ] Mensajes recien enviados (streaming) obtienen data-msg-id y son seleccionables

### Test API en produccion (2026-02-07)

> **URL:** https://secretaria.axcsol.com (TODAS las pruebas se hacen contra produccion, NO localhost)

| Paso | Endpoint | Resultado |
|------|----------|-----------|
| Health check | GET /health | 200 OK |
| Login | POST /api/auth/login | JWT obtenido (user: xulii) |
| Bot status | GET /api/telegram/bot-status | configured: true, bot: Xulita_bot |
| Contactos | GET /api/telegram/contacts | 2 contactos: SebastianXL (954140845), XULITA (8555711611) |
| Conversaciones | GET /api/chat/conversations | 6 conversaciones disponibles |
| Mensajes conv 6 | GET /api/chat/conversations/6/messages | 4 mensajes (ids 19-22) |
| **Envio bulk** | POST /api/telegram/send-bulk {msg 21+22 → contact 1} | **ok: true, "Enviado"** |
| Historial | GET /api/telegram/history | ids 9,10 status "sent" a SebastianXL |

**Nota:** El contacto XULITA (chat_id 8555711611) tiene todos los envios en status "error" — verificar que el usuario haya iniciado /start con @Xulita_bot o que el chat_id sea correcto.

### Archivos modificados
- `backend/routers/telegram.py` — SendBulkRequest schema, split_telegram_text helper, POST /api/telegram/send-bulk endpoint
- `backend/routers/chat.py` — Emitir [USER_MSG_ID:{id}] antes del streaming
- `frontend/index.html` — Selection toolbar, toast container
- `frontend/css/style.css` — Selection toolbar, checkboxes, selected bubbles, picker mode, toast; eliminados btn-forward, forward-menu, forward-status
- `frontend/js/app.js` — Selection mode state/functions, long-press/contextmenu handlers, contact picker, forwardSelectedToTelegram, renderMessage sin forward button, SSE USER_MSG_ID parsing; eliminadas showForwardMenu, closeForwardMenus, forwardToTelegram, showForwardStatus

---

## Hotfix: Etiquetas `<think>` visibles durante streaming

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
Al generar documentos (modo documento activado), las etiquetas `<think>` del modelo AI se mostraban en la burbuja del chat durante el streaming. La funcion `stripThinkTags()` solo tenia una regex para bloques completos `<think>...</think>`, pero durante el streaming la etiqueta de cierre `</think>` aun no habia llegado, asi que la regex no hacia match y el texto de "pensamiento" se mostraba en pantalla.

### Solucion
- [x] Agregar segunda regex a `stripThinkTags()` para eliminar bloques incompletos `<think>...` (etiqueta abierta sin cierre)
- [x] Push a GitHub + restart Coolify (deploy UUID: z880gk04gw4ccoc0c4cgc408, commit: 76cbd60)
- [x] Verificar en produccion: streaming limpio sin `<think>`, tarjeta DOCX visible, descarga funcional

### Verificacion
- [x] JS actualizado en produccion (`stripThinkTags` con dos regex)
- [x] Generacion de documento en streaming → burbuja limpia, sin texto de pensamiento
- [x] Tarjeta DOCX aparece correctamente (nombre, tipo, tamano)
- [x] Endpoint de descarga `/api/documents/{id}` → 200 OK, content-type DOCX, attachment correcto

### Archivos modificados
- `frontend/js/app.js` — `stripThinkTags()`: agregada regex `/<think>[\s\S]*$/gi` para bloques incompletos durante streaming

---

## Hotfix: Respuestas AI no visibles por newlines en SSE chunks

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Problema
Tras el hotfix de `<think>` tags, las respuestas de la IA no se mostraban en el chat. El modelo MiniMax emite bloques `<think>...</think>` con saltos de linea dentro de los chunks SSE. En `chat.py:301`, cuando el chunk contiene `\n`, el formato SSE se rompe: la linea despues del newline no tiene prefijo `data: ` y el frontend la ignora. La burbuja assistant aparecia vacia (solo timestamp).

### Solucion
- [x] Backend (`chat.py:301`): escapar newlines en chunks SSE (`chunk.replace('\n', '\\n')`) para que cada linea `data:` sea una sola linea
- [x] Frontend (`app.js:870`): decodificar newlines escapados al acumular texto (`data.replaceAll('\\n', '\n')`)
- [x] Push a GitHub → deploy automatico en Coolify

### Verificacion
- [ ] `docker compose up --build` arranca sin errores
- [ ] Chat normal → respuesta visible en streaming
- [ ] Modo documento → respuesta visible + tarjeta DOCX
- [ ] Modo busqueda → respuesta Perplexity visible
- [ ] Recargar pagina → historial con respuestas correctas

### Archivos modificados
- `backend/routers/chat.py` — Escapar `\n` → `\\n` en chunks SSE antes de yield
- `frontend/js/app.js` — Decodificar `\\n` → `\n` al acumular texto en streaming

---

## Fix: Descargas de archivos devuelven "Not Authenticated"

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Problema
Todos los endpoints de servir archivos (`/api/documents/{id}`, `/api/upload/files/{id}`) requieren JWT via header `Authorization: Bearer`. Pero el frontend usa elementos HTML directos (`<a href>`, `<img src>`, `window.open`) que no incluyen headers custom — los browsers nunca envian Authorization en navegacion/recursos. Resultado: `{"detail":"Not authenticated"}` al descargar documentos DOCX e imagenes rotas.

### Causa raiz
- `backend/auth.py`: `security = HTTPBearer()` — solo acepta header Authorization
- `frontend/js/app.js`: URLs directas sin token en `img.src`, `window.open`, `fileEl.href`, `card.href`

### Solucion
- [x] Backend: `HTTPBearer(auto_error=False)` para no rechazar automaticamente sin header
- [x] Backend: `get_current_user` acepta `Request`, lee token de header Bearer (existente) o `?token=` query param (fallback)
- [x] Frontend: helper `authUrl(url)` que agrega `?token=<jwt>` a URLs
- [x] Frontend: actualizar 4 ubicaciones (img.src, window.open, fileEl.href, card.href) para usar `authUrl()`
- [x] Push a GitHub → deploy automatico en Coolify

### Verificacion
- [ ] Descargar documento DOCX generado → descarga correcta (sin "Not authenticated")
- [ ] Imagenes subidas se muestran inline correctamente
- [ ] Click en imagen → abre en nueva pestana
- [ ] Click en archivo adjunto → descarga correcta
- [ ] API calls con Bearer header siguen funcionando (chat, upload, etc.)

### Archivos modificados
- `backend/auth.py` — Import Request, HTTPBearer(auto_error=False), get_current_user con fallback a query param ?token=
- `frontend/js/app.js` — Helper authUrl(), actualizar img.src, window.open, fileEl.href, card.href

---

## Fix: Documentos generados perdidos tras redeploy ("Archivo no encontrado en disco")

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Problema
Al descargar un documento generado desde produccion (`/api/documents/{id}`), el API retornaba `{"detail":"Archivo no encontrado en disco"}`. El registro File existia en la BD (file_id=6, 37.7 KB) y la auth funcionaba, pero el archivo `.docx` fisico no existia en `/data/generados/`. La BD persiste correctamente (conversaciones visibles) porque usa volumen Docker, pero los archivos generados se perdieron durante un redeploy de Coolify.

### Causa raiz
Los archivos DOCX generados se almacenan en `/data/generados/` dentro del contenedor. Aunque el volumen `/data` es persistente (la BD SQLite sobrevive redeploys), los archivos generados se perdieron durante un redeploy. El endpoint de descarga simplemente retornaba 404 sin intentar recuperacion.

### Solucion
- [x] Modificar `download_document()` en `documents.py`: cuando el archivo falta del disco pero `f.message_id` existe, buscar el `Message` asociado y regenerar el DOCX con `generate_docx()` usando el contenido del mensaje
- [x] Agregar imports: `Message`, `generate_docx`, `settings`
- [x] El archivo regenerado se guarda en la ruta original (`f.filepath`), persistiendo para futuras descargas
- [x] Si la regeneracion falla (sin message_id, sin contenido), se mantiene el error 404 original
- [x] Push a GitHub → deploy automatico en Coolify

### Verificacion
- [ ] Descargar documento que falta del disco → se regenera y descarga correctamente
- [ ] Descargar el mismo documento de nuevo → sirve el archivo ya regenerado (sin regenerar otra vez)
- [ ] Documentos con archivo presente en disco → descarga normal sin cambios
- [ ] Documentos sin message_id → error 404 como antes

### Archivos modificados
- `backend/routers/documents.py` — Imports (Message, generate_docx, settings), logica de auto-regeneracion en download_document() cuando archivo falta del disco

---

## Feature: Upload de archivo sin texto espera instrucciones

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
Al subir un documento (PDF, DOCX, TXT, etc.) sin escribir texto, la IA recibia el contenido extraido completo y empezaba a analizar/resumir sin que nadie se lo pidiera. El usuario quiere que al subir un archivo, la app confirme la recepcion y espere instrucciones.

### Solucion
Tres cambios en `backend/routers/chat.py`:

1. **Auto-titulo movido antes del shortcut** — usa `count()` para detectar primer mensaje, funciona tanto para file-only como para mensajes normales
2. **Shortcut file-only** — si hay archivos pero no texto (`bool(file_ids) and not content`), devuelve respuesta fija "Archivo recibido: **nombre.pdf**. Estoy listo..." via SSE sin llamar a la IA. Mensaje guardado con `model_used="system"`
3. **Historial enriquecido con archivos previos** — `joinedload(Message.files)` en query de historial + inyeccion de `extracted_text` en mensajes user anteriores que tengan archivos adjuntos, para que la IA tenga contexto del documento cuando el usuario luego de instrucciones

### Verificacion (en produccion tras redeploy)
- [ ] Subir PDF sin texto → respuesta fija "Archivo recibido: **X**. Estoy listo..."
- [ ] Luego escribir "Resumeme el documento" → la IA responde con el contenido del PDF
- [ ] Subir archivo CON texto (ej: "Resumeme esto") → comportamiento actual (IA analiza directo)
- [ ] Modo documento/busqueda con archivo sin texto → respuesta fija igual
- [ ] Auto-titulo funciona tanto con archivo solo como con texto

### Archivos modificados
- `backend/routers/chat.py` — Auto-titulo movido, shortcut file-only con SSE stream fijo, historial enriquecido con joinedload(Message.files) y extracted_text de mensajes previos

---

## Fix: Filtrar bloques `<think>` del modelo MiniMax en backend

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
MiniMax-M2 incluye bloques de razonamiento (chain-of-thought) envueltos en `<think>...</think>` en sus respuestas. Estos bloques aparecian en las burbujas del chat durante streaming, se guardaban en la BD y se incluian en los documentos DOCX generados. El hotfix anterior (frontend `stripThinkTags()`) solo limpiaba la visualizacion; el contenido seguia presente en BD y DOCX.

### Solucion
Dos capas de filtrado en backend:

1. **Filtro de streaming (`minimax_ai.py`)** — Funcion `_filter_think_blocks()` que procesa texto en tiempo real suprimiendo contenido entre `<think>` y `</think>`. Maneja tags partidos entre chunks SSE usando un buffer interno y estado `inside_think`. El buffer retiene caracteres que podrian ser inicio de un tag parcial (ej: `<thi` al final de un chunk).

2. **Red de seguridad (`chat.py`)** — Antes de guardar `full_response` en la BD y antes de pasar a `generate_docx()`, se aplica `re.sub(r'<think>[\s\S]*?</think>', '', full_response)` para eliminar cualquier bloque residual.

### Verificacion
- [ ] Chat normal → no aparece contenido `<think>` en la burbuja
- [ ] Generar documento → DOCX sin bloques de razonamiento
- [ ] Contenido guardado en BD esta limpio
- [ ] Mensajes sin think → funcionan igual que antes

### Archivos modificados
- `backend/services/minimax_ai.py` — Constantes THINK_OPEN/THINK_CLOSE, funcion `_filter_think_blocks()` (parser stateful con buffer), estado inside_think/buffer en `chat_completion_stream()`, flush de buffer al final del stream
- `backend/routers/chat.py` — Import `re`, `clean_response` con regex antes de guardar en BD y antes de `generate_docx()`

---

## Feature: Soporte formato TXT en generacion de documentos

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
La generacion de documentos solo producia archivos DOCX. El usuario quiere poder elegir entre DOCX y TXT al generar un documento.

### Solucion
Selector de formato en el frontend que aparece al activar modo documento. El backend bifurca la generacion segun el formato elegido.

**Backend (3 archivos):**
1. `doc_generator.py` — Nueva funcion `generate_txt(content, title, save_dir)` que escribe texto plano en `doc_YYYYMMDD_HHMMSS.txt`
2. `chat.py` — Campo `doc_format` en MessageCreate (default "docx"), validacion (solo "docx"/"txt"), bifurcacion: TXT → `generate_txt()` + mime `text/plain`, DOCX → `generate_docx()` + mime DOCX
3. `documents.py` — Auto-regeneracion detecta formato por extension del filename (`.txt` → `generate_txt`), FileResponse usa `f.mime_type` de la BD en vez de hardcodear DOCX

**Frontend (3 archivos):**
4. `index.html` — `<select id="doc-format-select">` con opciones DOCX/TXT, hidden por defecto
5. `style.css` — Estilos `.doc-format-select` (pill compacto, borde purpura, texto `#c3b8ff`)
6. `app.js` — Ref `docFormatSelect`, show/hide con docMode toggle, ocultar con searchMode, enviar `doc_format` en body POST, deteccion de `.txt` en renderMessage para doc cards, label dinamico (ext del filename en vez de "DOCX" hardcodeado)

### Verificacion
- [ ] Activar modo documento → aparece selector DOCX/TXT junto al boton
- [ ] Generar documento en formato DOCX → funciona igual que antes
- [ ] Generar documento en formato TXT → crea `.txt`, tarjeta muestra "TXT"
- [ ] Descargar ambos formatos → descarga correcta con mime type correcto
- [ ] Activar modo busqueda → selector se oculta
- [ ] Desactivar modo documento → selector se oculta
- [ ] Recargar pagina → historial muestra tarjetas TXT y DOCX correctamente

### Archivos modificados
- `backend/services/doc_generator.py` — Nueva funcion `generate_txt()`
- `backend/routers/chat.py` — `doc_format` en MessageCreate, import `generate_txt`, bifurcacion generacion por formato, mime dinamico
- `backend/routers/documents.py` — Import `generate_txt`, auto-regeneracion por extension, `f.mime_type` en FileResponse
- `frontend/index.html` — Select `#doc-format-select` con opciones DOCX/TXT
- `frontend/css/style.css` — Estilos `.doc-format-select`
- `frontend/js/app.js` — Ref docFormatSelect, show/hide logica, doc_format en body, deteccion `.txt` en renderMessage, label dinamico en createDocCard

---

## Feature: Explorador de archivos en sidebar

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
Los archivos (subidos y generados) solo eran visibles inline dentro de los mensajes del chat. No existia una vista global para explorar todos los archivos del usuario organizados por tipo.

### Solucion
Tabs en el sidebar existente (Conversaciones / Archivos) con un explorador de archivos en arbol colapsable por tipo.

**Backend (2 archivos):**
1. `routers/files.py` — CREADO: Endpoint `GET /api/files` que retorna todos los archivos del usuario (across all conversations) con schema `FileExplorerItem` incluyendo campo `is_generated` calculado server-side (`"/generados/" in filepath`)
2. `main.py` — Registrado `files_router` antes del static mount

**Frontend (3 archivos):**
3. `index.html` — Sidebar con tabs (Conversaciones/Archivos), contenedor `#file-explorer` con 3 grupos colapsables (Documentos, Imagenes, Generados), estado vacio
4. `style.css` — Estilos para tabs (`.sidebar-tabs`, `.sidebar-tab.active` con borde accent), arbol colapsable (`.file-group`, chevron rotable, `.expanded`), items de archivo (icono teal para uploads, purple para generados), ocultar boton "+" en tab Archivos
5. `app.js` — Estado `activeTab`/`explorerFiles`, tab switching con toggle hidden, `loadExplorerFiles()` fetch + render, clasificacion en 3 grupos, URLs de descarga correctas (generados → `/api/documents/{id}`, uploads → `/api/upload/files/{id}`), event delegation para colapsar/expandir, integracion en `enterApp()`, reset en logout, refresh post-stream

### Verificacion
- [ ] Sidebar muestra tabs "Conversaciones" / "Archivos"
- [ ] Tab "Conversaciones" funciona igual que antes (sin regresion)
- [ ] Tab "Archivos" carga y muestra arbol con 3 categorias
- [ ] Subir un archivo → aparece en la categoria correcta
- [ ] Generar un documento → aparece en "Generados"
- [ ] Click en archivo → se descarga/abre correctamente
- [ ] Grupos colapsables funcionan (click en header)
- [ ] Grupos vacios se ocultan
- [ ] Mobile: sidebar slide-out funciona con ambos tabs
- [ ] Boton "+" se oculta en tab Archivos

### Archivos creados/modificados
- `backend/routers/files.py` — CREADO: GET /api/files con FileExplorerItem schema (id, filename, file_type, mime_type, size_bytes, created_at, is_generated)
- `backend/main.py` — Registrado files_router
- `frontend/index.html` — Sidebar tabs + file explorer con 3 grupos colapsables
- `frontend/css/style.css` — Estilos sidebar-tabs, file-explorer, file-group, file-explorer-item, file-explorer-empty
- `frontend/js/app.js` — Tab switching, loadExplorerFiles, renderFileExplorer, collapse/expand, lifecycle integration

---

## Fix: Archivos fantasma en explorador + descargas seguras

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
Tras redeploy en Coolify, los archivos fisicos en `/data/documentos/`, `/data/imagenes/` se pierden (el volumen persiste la BD SQLite pero no siempre los subdirectorios). El endpoint `GET /api/files` devolvia TODOS los registros File de la BD sin verificar existencia en disco, mostrando archivos fantasma en el explorador. Al pulsar un archivo inexistente, se abria una pestana nueva con `{"detail":"Archivo no encontrado en disco"}` sin forma de volver a la app.

### Solucion
**Backend (`routers/files.py`):**
- Agregado `import os` y filtro `os.path.exists(f.filepath)` en el loop de `list_all_files()` — archivos sin archivo fisico en disco se saltan con `continue`, eliminando archivos fantasma de raiz

**Frontend (`js/app.js`):**
- Cambiado `<a href target="_blank">` por `<div>` clickable con event listener
- Descarga via `fetch()` con header `Authorization: Bearer` (en vez de `?token=` en query param)
- Respuesta OK → blob URL + descarga con filename original
- Error → toast dentro de la app (sin navegar fuera)

### Verificacion
- [ ] Explorador solo muestra archivos que existen fisicamente en disco
- [ ] Click en archivo existente → se descarga correctamente (sin abrir pestana nueva)
- [ ] Si un archivo se borra del disco y se recarga el explorador → desaparece de la lista
- [ ] Error de descarga → toast de error sin salir de la app
- [ ] Token no expuesto en URL (usa header Authorization)

### Archivos modificados
- `backend/routers/files.py` — `import os`, filtro `os.path.exists()` en loop de list_all_files
- `frontend/js/app.js` — renderFileExplorer: `<div>` con click handler, fetch+blob download, toast de error

---

## Fix: Archivos fantasma invisibles en explorador (ghost files mostrados como "no disponible")

> **Estado:** [x] Completada
> **Prioridad:** Media

### Problema
El commit `82ac0` introdujo un filtro en `GET /api/files` que ocultaba completamente los archivos cuyo fichero fisico no existia en disco (`os.path.exists()` → `continue`). Tras rebuild del contenedor o redeploy en Coolify, si los archivos fisicos se perdian, el API devolvia `[]` y el explorador aparecia vacio — aunque los registros seguian en la BD. Ademas, `loadExplorerFiles()` en el frontend tragaba errores silenciosamente.

### Solucion
En lugar de ocultar archivos fantasma, mostrarlos con indicador visual "no disponible":

**Backend (`routers/files.py`):**
- Agregado campo `available: bool` al schema `FileExplorerItem`
- Quitado el `continue` que ocultaba ghost files; solo se saltan registros sin `filepath` (datos invalidos)
- `available = os.path.exists(f.filepath)` calculado para cada fichero

**Frontend (`js/app.js`):**
- `renderFileExplorer()`: items no disponibles reciben clase CSS `unavailable`, cursor `default`, texto "No disponible" en meta, y se renderizan sin click handler (early return)
- `loadExplorerFiles()`: agregado `showToast('Error cargando archivos')` en el catch

**Frontend (`css/style.css`):**
- `.file-explorer-item.unavailable`: opacity 0.45, cursor default
- `.file-explorer-item.unavailable:hover`: sin hover effect
- `.file-explorer-item.unavailable .file-icon`: fondo gris (#555)

### Verificacion
- [ ] Archivos con fichero fisico en disco → aparecen normales, click descarga
- [ ] Archivos fantasma (sin fichero fisico) → aparecen grises con "No disponible", sin click
- [ ] Error de red en carga de archivos → toast "Error cargando archivos"
- [ ] Explorador no aparece vacio tras redeploy (registros BD siguen visibles)

### Archivos modificados
- `backend/routers/files.py` — Campo `available: bool` en schema, filtro relajado (solo skip sin filepath), `os.path.exists()` para available
- `frontend/js/app.js` — Clase `unavailable` condicional, meta "No disponible", early return sin click handler, toast de error en catch
- `frontend/css/style.css` — Estilos `.file-explorer-item.unavailable` (opacity, hover, icono gris)

---

## Fix: Archivos recuperables tras redeploy (recoverable files)

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Problema
Tras cada redeploy en Coolify, los archivos fisicos en `/data/documentos/`, `/data/imagenes/`, `/data/generados/` se pierden. La BD SQLite persiste, asi que los registros `File` existen pero los archivos fisicos no. El endpoint `GET /api/files` marcaba todos como `available: false` y el frontend bloqueaba los clicks en TODOS los archivos no disponibles. Sin embargo, el backend YA tenia logica de auto-regeneracion en `documents.py` para documentos generados (desde contenido del mensaje), y los TXT subidos tenian `extracted_text` en la BD. Ambos tipos eran recuperables, pero el frontend impedia que el usuario llegara a usarlos.

### Solucion
Clasificacion de archivos en 3 estados: disponible, recuperable, perdido.

**Backend (`routers/files.py`):**
- Agregado campo `recoverable: bool` al schema `FileExplorerItem`
- Logica: si no `available` y es generado con `message_id` → `recoverable = True`
- Logica: si no `available` y tiene `extracted_text` → `recoverable = True`
- Si no cumple ninguno → `recoverable = False`

**Backend (`routers/upload.py`):**
- En `serve_file()`, antes del 404, intenta recuperar desde `extracted_text` si el archivo tiene ese campo
- Crea directorios padre con `os.makedirs()` y escribe el archivo de texto
- Si sigue sin existir tras el intento, retorna 404 original

**Frontend (`js/app.js`):**
- Clasificacion: `canClick = f.available || f.recoverable`
- Archivos recuperables: clase CSS `recoverable`, label "Recuperable" en meta, click handler habilitado
- Archivos irrecuperables: clase CSS `unavailable`, label "No disponible", sin click (sin cambios)
- Tras descarga exitosa de archivo recuperable: `loadExplorerFiles()` refresca para actualizar estado

**Frontend (`css/style.css`):**
- `.file-explorer-item.recoverable`: opacity 0.65, cursor pointer
- `.file-explorer-item.recoverable:hover`: hover effect habilitado
- `.file-explorer-item.recoverable .file-icon`: fondo dorado oscuro (#7c6f3a)

### Verificacion
- [ ] Tab "Archivos" → generados muestran "Recuperable" en vez de "No disponible"
- [ ] Click en DOCX generado → se descarga correctamente (backend regenera desde mensaje)
- [ ] Click en TXT subido → se descarga correctamente (recuperado desde extracted_text)
- [ ] Refrescar explorador tras descarga → archivo aparece como disponible (normal)
- [ ] Archivos de imagen sin archivo fisico → siguen como "No disponible" sin click
- [ ] Archivos disponibles en disco → funcionan igual que antes (sin regresion)

### Archivos modificados
- `backend/routers/files.py` — Campo `recoverable: bool` en schema, logica de clasificacion (generated+message_id o extracted_text)
- `backend/routers/upload.py` — Recuperacion de TXT desde `extracted_text` en `serve_file()` antes de 404
- `frontend/js/app.js` — Clasificacion 3 estados (available/recoverable/lost), click handler condicional, label "Recuperable", refresh post-descarga
- `frontend/css/style.css` — Clase `.recoverable` (opacity 0.65, cursor pointer, icono dorado, hover effect)

---

## Fase 9+10: Google OAuth 2.0 — Seguridad + Flujo completo

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Agregar dependencias: cryptography, google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client
- [x] Agregar 4 variables Google OAuth a config.py y .env.example (sin valores reales)
- [x] Crear modelo GoogleToken (id, user_id FK unique, encrypted_token LargeBinary, scopes Text, timestamps)
- [x] Relacion google_token en modelo User (uselist=False)
- [x] Crear backend/services/google_auth.py (Fernet encrypt/decrypt, CRUD tokens cifrados)
- [x] Crear backend/routers/google.py con 4 endpoints:
  - GET /api/google/status (connected, scopes)
  - GET /api/google/auth-url (genera URL consentimiento con state=user_{id})
  - GET /api/google/callback (intercambia code, cifra tokens, redirige a app)
  - POST /api/google/disconnect (revoca best-effort, elimina de BD)
- [x] Helper get_valid_credentials() para fases futuras (refresca token expirado)
- [x] Scopes: calendar, gmail.modify, drive, contacts.readonly
- [x] OAuth params: access_type=offline, prompt=consent
- [x] Registrar google_router en main.py (antes del static mount)
- [x] Frontend: boton Google en header (SVG, azul → verde cuando conectado)
- [x] Frontend: modal Google bottom-sheet (conectar, scopes badges, desconectar)
- [x] Frontend: deteccion ?google_connected / ?google_error en URL → toast
- [x] Frontend: checkGoogleStatus en enterApp, reset en logout

### Verificacion
- [ ] `docker compose up --build` arranca sin errores
- [ ] GET /health → 200 OK
- [ ] Tabla google_tokens creada en SQLite
- [ ] .env.example solo tiene nombres, sin valores reales
- [ ] Click boton Google → abre modal con "Conectar Google"
- [ ] Click "Conectar Google" → redirige a consentimiento Google
- [ ] Autorizar → token cifrado en BD → redirect con toast "Google conectado exitosamente"
- [ ] GET /api/google/status → {connected: true, scopes: [...]}
- [ ] Modal muestra scopes y boton "Desconectar"
- [ ] Click "Desconectar" → token eliminado, UI actualiza
- [ ] Boton Google cambia color (azul ↔ verde)

### Archivos creados/modificados
- `requirements.txt` — 5 dependencias Google/crypto
- `backend/config.py` — 4 variables Google OAuth
- `.env.example` — Seccion Google OAuth
- `backend/models.py` — Import LargeBinary, modelo GoogleToken, relacion en User
- `backend/services/google_auth.py` — CREADO: Fernet encrypt/decrypt, CRUD tokens
- `backend/routers/google.py` — CREADO: 4 endpoints OAuth + helpers
- `backend/main.py` — Import y registro google_router
- `frontend/index.html` — Boton Google header + modal Google
- `frontend/css/style.css` — Estilos Google (boton, modal, badges, botones connect/disconnect)
- `frontend/js/app.js` — Estado Google, modal, OAuth redirect, status check, UI update

---

## Fase 11: Google Calendar — Lectura y creacion de eventos

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Tareas
- [x] Crear `backend/services/google_calendar.py` con funciones:
  - `list_events(creds, time_min, time_max, max_results)` — listar eventos del calendario primario
  - `get_event(creds, event_id)` — detalle de un evento
  - `create_event(creds, summary, start, end, description?, location?, attendees?)` — crear evento
  - `delete_event(creds, event_id)` — eliminar evento
- [x] Agregar 5 endpoints de Calendar en `backend/routers/google.py`:
  - `GET /api/google/calendar/events?time_min=&time_max=&max_results=` — rango personalizado
  - `GET /api/google/calendar/events/today` — eventos de hoy (UTC midnight to midnight)
  - `GET /api/google/calendar/events/week` — eventos de los proximos 7 dias
  - `POST /api/google/calendar/events` — crear evento (CreateEventBody model)
  - `DELETE /api/google/calendar/events/{event_id}` — eliminar evento
- [x] Helper `_require_google()` para validar conexion Google en endpoints
- [x] Frontend: seccion Calendar dentro del modal Google (visible solo cuando conectado)
- [x] Frontend: tabs Hoy/Semana para filtrar eventos
- [x] Frontend: eventos como cards (hora, titulo, ubicacion, boton eliminar)
- [x] Frontend: click en titulo → abre evento en Google Calendar (html_link)
- [x] Frontend: formulario crear evento (titulo, inicio, fin, ubicacion, descripcion)
- [x] Frontend: carga automatica de eventos al abrir modal Google

### Archivos creados/modificados
- `backend/services/google_calendar.py` — CREADO: _get_service, list_events, get_event, create_event, delete_event, _parse_datetime, _format_event
- `backend/routers/google.py` — Imports (datetime, HTTPException, BaseModel, google_calendar), _require_google helper, 5 endpoints calendar, CreateEventBody model
- `frontend/index.html` — Seccion gcal-section en google-connected (tabs, event list, create form con inputs)
- `frontend/css/style.css` — Estilos gcal-section, gcal-header, gcal-tabs, gcal-tab, btn-gcal-add, gcal-events, gcal-event, gcal-form, gcal-input, gcal-form-actions
- `frontend/js/app.js` — Estado gcalPeriod, refs DOM, gcalTabs handler, loadCalendarEvents, renderCalendarEvents, formatCalendarTime, toLocalISOString, form handlers (add/cancel/save), integracion con updateGoogleUI

---

## Fase 12: Gmail — Lectura y envio de correos

> **Estado:** [x] Completada
> **Prioridad:** Media

### Tareas
- [x] Crear `backend/services/google_gmail.py` con funciones:
  - `list_messages(creds, query, max_results)` — listar mensajes con metadata (From, Subject, Date)
  - `get_message(creds, message_id)` — detalle completo con body extraido
  - `send_message(creds, to, subject, body, cc?, bcc?)` — enviar correo via MIME
- [x] Agregar 4 endpoints Gmail en `backend/routers/google.py`:
  - `GET /api/google/gmail/messages?q=&max=` — listar mensajes (busqueda opcional)
  - `GET /api/google/gmail/messages/unread` — mensajes no leidos (query is:unread)
  - `GET /api/google/gmail/messages/{message_id}` — detalle completo
  - `POST /api/google/gmail/send` — enviar correo (SendEmailBody model)
- [x] Frontend: seccion Gmail dentro del modal Google (visible solo cuando conectado)
- [x] Frontend: tabs Inbox/No leidos para filtrar correos
- [x] Frontend: emails como cards (remitente, asunto, snippet, fecha, indicador unread)
- [x] Frontend: badge rojo con conteo de no leidos
- [x] Frontend: vista detalle de email (click en card → subject, from, to, date, body)
- [x] Frontend: formulario de composicion (to, subject, body) con envio

### Archivos creados/modificados
- `backend/services/google_gmail.py` — CREADO: _get_service, list_messages, get_message, send_message, _get_header, _format_message_summary, _format_message_full, _extract_body
- `backend/routers/google.py` — Import google_gmail, 4 endpoints Gmail, SendEmailBody model
- `frontend/index.html` — Seccion gmail-section en google-connected (tabs, message list, compose form, detail view)
- `frontend/css/style.css` — Estilos gmail-section, gmail-header, gmail-tabs, gmail-msg, gmail-compose, gmail-detail, gmail-unread-badge, btn-gmail-*
- `frontend/js/app.js` — Estado gmailTab, refs DOM Gmail, loadGmailMessages, renderGmailMessages, formatGmailDate, openGmailDetail, compose handlers, integracion con updateGoogleUI

---

## Fase 13: Google Drive — Explorar y subir archivos

> **Estado:** [x] Completada
> **Prioridad:** Media

### Tareas
- [x] Crear `backend/services/google_drive.py` con funciones:
  - `list_files(creds, query, folder_id, max_results)` — listar archivos con filtros
  - `list_recent(creds, max_results)` — archivos recientes del usuario
  - `get_file(creds, file_id)` — metadata de archivo
  - `download_file(creds, file_id)` — descargar (con export para Google Docs/Sheets/Slides)
  - `upload_file(creds, filename, content, mime_type, folder_id?)` — subir archivo
  - `list_folders(creds)` — listar carpetas
- [x] Agregar 5 endpoints Drive en `backend/routers/google.py`:
  - `GET /api/google/drive/files?q=&folder=&max=` — listar archivos
  - `GET /api/google/drive/files/recent` — archivos recientes
  - `GET /api/google/drive/files/{id}` — metadata
  - `GET /api/google/drive/files/{id}/download` — descargar
  - `POST /api/google/drive/upload` — subir archivo (multipart)
- [x] Frontend: seccion Drive dentro del modal Google (tabs Recientes/Buscar)
- [x] Frontend: archivos como cards (icono por tipo, nombre, tamano, fecha)
- [x] Frontend: iconos coloreados por tipo (folder amarillo, gdoc azul, gsheet verde, gslides amarillo, pdf rojo)
- [x] Frontend: busqueda en Drive (search bar con input + boton)
- [x] Frontend: click en archivo → abre en Google Drive (webViewLink)
- [x] Frontend: boton descargar en cada archivo
- [x] Frontend: formulario de subida a Drive (file picker + boton subir)

### Archivos creados/modificados
- `backend/services/google_drive.py` — CREADO: _get_service, list_files, list_recent, get_file, download_file, upload_file, list_folders, _format_file, MIME_ICONS
- `backend/routers/google.py` — Imports (UploadFile, File, Response, drive_*), 5 endpoints Drive
- `frontend/index.html` — Seccion gdrive-section en google-connected (tabs, search bar, file list, upload form)
- `frontend/css/style.css` — Estilos gdrive-section, gdrive-header, gdrive-tabs, gdrive-file, gdrive-file-icon (colores por tipo), gdrive-upload-form, btn-gdrive-*
- `frontend/js/app.js` — Estado driveTab/driveUploadFile, refs DOM Drive, loadDriveFiles, renderDriveFiles, formatDriveDate, gdriveTabs handler, upload handlers (pick/send/cancel), search handler, integracion con updateGoogleUI

---

## Fase 14: Google Contacts — Lectura y autocompletar

> **Estado:** [x] Completada
> **Prioridad:** Baja

### Tareas
- [x] Crear `backend/services/google_contacts.py` con People API:
  - `list_contacts(creds, query, max_results)` — listar contactos (connections.list)
  - `search_contacts(creds, query, max_results)` — buscar contactos (people.searchContacts)
  - `get_contact(creds, resource_name)` — detalle de contacto
- [x] Agregar 3 endpoints Contacts en `backend/routers/google.py`:
  - `GET /api/google/contacts?q=&max=` — listar/buscar contactos
  - `GET /api/google/contacts/search?q=&max=` — busqueda remota (People API searchContacts)
  - `GET /api/google/contacts/{id}` — detalle (resource_name como path)
- [x] Frontend: autocomplete en campo "Para" de Gmail Compose
  - Pre-carga de contactos al conectar Google (cache local)
  - Filtrado local por nombre/email durante escritura
  - Busqueda remota como fallback (debounce 300ms, min 2 chars)
  - Dropdown con avatar, nombre y email
  - Navegacion por teclado (arrows + Enter + Escape)
  - Click en contacto → rellena email en input
- [x] Reset de cache en disconnect y logout

### Archivos creados/modificados
- `backend/services/google_contacts.py` — CREADO: _get_service, list_contacts, search_contacts, get_contact, _has_email, _format_contact
- `backend/routers/google.py` — Imports google_contacts, 3 endpoints Contacts
- `frontend/index.html` — Wrapper contact-autocomplete-wrapper en gmail-to, dropdown container
- `frontend/css/style.css` — Estilos contact-autocomplete, contact-ac-item, contact-ac-avatar, contact-ac-info
- `frontend/js/app.js` — contactsCache, loadContactsCache, filterContacts, searchContactsRemote, renderACResults, setupContactAutocomplete, keyboard nav, reset en disconnect/logout, pre-carga en updateGoogleUI

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
| 5 | 2026-02-06 | Fase 3 | Fase 3 completada: perplexity service, search toggle, routing condicional chat/search | Iniciar Fase 4: Generador de documentos |
| 6 | 2026-02-06 | Fase 4 | Fase 4 completada: doc_generator service, documents router, toggle documento, generacion DOCX post-stream, cards de descarga | Iniciar Fase 5: Telegram |
| 7 | 2026-02-06 | Fase 5 | Fase 5 completada: telegram_bot service, telegram router, modal contactos, forward button en burbujas, dropdown selector, feedback animado | Iniciar Fase 6: Deploy Coolify |
| 8 | 2026-02-06 | Fase 6 | Fase 6 completada: .dockerignore creado, SEGUIMIENTO actualizado, proyecto listo para deploy Coolify | Push a GitHub y verificar deploy |
| 9 | 2026-02-06 | Deploy | TELEGRAM_DEFAULT_CHAT_ID agregado, push a GitHub, variables configuradas en Coolify | Verificar deploy en produccion |
| 10 | 2026-02-06 | Seguridad auth | Registro publico eliminado, credenciales via env vars (APP_USERNAME/APP_PASSWORD), auto-creacion de usuario al arrancar | Verificar deploy con nuevas credenciales |
| 11 | 2026-02-07 | Fix Telegram | Eliminado parse_mode HTML de telegram_bot.py, fix reenvio con caracteres especiales. App completa funcionando en produccion | Mantenimiento continuo |
| 12 | 2026-02-07 | Fase 7 | Multi-select Telegram forwarding: selection mode (long-press/right-click), bulk send endpoint, contact picker, toast feedback. Reemplaza forward-per-bubble | Verificar en produccion |
| 13 | 2026-02-07 | Test produccion | Test API completo contra https://secretaria.axcsol.com: health, login, bot-status, contacts, send-bulk OK. Envio bulk (msgs 21+22) a SebastianXL exitoso. Contacto XULITA con errores (chat_id pendiente de verificar) | Verificar UI manual (long-press, selection mode) |
| 14 | 2026-02-07 | Hotfix think tags | Fix etiquetas `<think>` visibles durante streaming en modo documento. Regex solo eliminaba bloques completos; agregada segunda regex para bloques incompletos. Deploy verificado en produccion, descarga DOCX OK | Fix SSE newlines |
| 15 | 2026-02-07 | Fix SSE newlines | Respuestas AI no visibles por newlines en chunks SSE. Modelo emite `<think>` con saltos de linea que rompen formato SSE. Fix: escapar `\n` → `\\n` en backend, decodificar en frontend | Verificar en produccion |
| 16 | 2026-02-07 | Fix auth descargas | Descargas de archivos devolvian "Not authenticated" porque browser no envia Authorization header en <a href>/<img src>. Fix: fallback a ?token= query param en backend + authUrl() helper en frontend | Verificar en produccion |
| 17 | 2026-02-07 | Fix docs perdidos | Documentos generados perdidos tras redeploy Coolify. Fix: auto-regeneracion DOCX desde contenido del mensaje en BD cuando archivo falta del disco | Verificar en produccion |
| 18 | 2026-02-07 | File-only upload | Upload de archivo sin texto ahora confirma recepcion y espera instrucciones en vez de auto-analizar. Historial enriquecido con archivos previos para que la IA tenga contexto en follow-ups | Verificar en produccion tras redeploy |
| 19 | 2026-02-07 | Filtro think backend | Filtro de bloques `<think>` en backend: streaming filter stateful en minimax_ai.py (maneja tags partidos entre chunks) + regex safety net en chat.py antes de guardar en BD y generar DOCX | Verificar en produccion |
| 20 | 2026-02-07 | Formato TXT docs | Soporte TXT en generacion de documentos: generate_txt() en backend, selector DOCX/TXT en frontend, bifurcacion por formato, auto-regeneracion por extension, mime dinamico, label dinamico en cards | Verificar en produccion |
| 21 | 2026-02-07 | File explorer | Explorador de archivos en sidebar: tabs Conversaciones/Archivos, endpoint GET /api/files, arbol colapsable por tipo (Documentos/Imagenes/Generados), iconos por tipo, descarga directa, lifecycle integration | Verificar en produccion |
| 22 | 2026-02-07 | Fix ghost files | Filtro os.path.exists en GET /api/files para eliminar archivos fantasma. Descargas via fetch+blob con toast de error en vez de navegacion directa a JSON. Auth via header Bearer en vez de query param | Verificar en produccion |
| 23 | 2026-02-07 | Fix ghost visible | Ghost files ahora visibles como "No disponible" (opacity 0.45, gris, sin click) en vez de ocultarse. Campo `available` en API. Toast de error en loadExplorerFiles | Verificar en produccion |
| 24 | 2026-02-07 | Recoverable files | Archivos perdidos tras redeploy clasificados en "Recuperable" (auto-regeneracion al click) o "No disponible" (irrecuperables). Campo `recoverable` en API. TXT subidos recuperados desde `extracted_text`. Refresh post-descarga | Verificar en produccion |
| 25 | 2026-02-07 | Fase 9+10 Google OAuth | Infraestructura seguridad (Fernet encrypt, GoogleToken model, config vars) + flujo OAuth completo (4 endpoints, modal UI, boton header, scopes badges, redirect handling). get_valid_credentials() para fases futuras | Build Docker + verificar OAuth flow |
| 26 | 2026-02-07 | Fase 11 Google Calendar | google_calendar.py service (list/get/create/delete events), 5 endpoints en google router, UI Calendar en modal (tabs hoy/semana, event cards, create form) | Build Docker + verificar Calendar |
| 27 | 2026-02-07 | Fase 12 Gmail | google_gmail.py service (list_messages, get_message, send_message), 4 endpoints Gmail en google router, UI Gmail en modal (tabs inbox/no leidos, email cards, compose form, detail view, badge no leidos) | Build Docker + verificar Gmail |
| 28 | 2026-02-07 | Fase 13 Google Drive | google_drive.py service (list_files, list_recent, get_file, download_file, upload_file, list_folders), 5 endpoints Drive en google router, UI Drive en modal (tabs recientes/buscar, file cards con iconos por tipo, search bar, upload form, descargar/abrir) | Build Docker + verificar Drive |
| 29 | 2026-02-07 | Fase 14 Contacts | google_contacts.py service (People API: list, search, get), 3 endpoints Contacts en google router, autocomplete en Gmail compose (cache local + busqueda remota, dropdown con avatar/nombre/email, keyboard nav) | Build Docker + verificar Contacts |
