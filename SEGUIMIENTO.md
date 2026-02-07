# SEGUIMIENTO - Secretaria

> **Objetivo:** Aplicación web mobile-first de asistente personal (secretaria) con chat continuo, gestión documental, generación de documentos y reenvío por Telegram
> **Carpeta:** D:\MINIMAX\Secretaria
> **Ultima actualizacion:** 2026-02-07
> **Estado global:** Fase 7 completada + Explorador de archivos en sidebar

---

## Resumen ejecutivo

Proyecto nuevo. Se ha definido la arquitectura, el stack técnico y las 7 fases de desarrollo. El cerebro es MINIMAX AI (chat) + Perplexity (búsqueda externa). La interfaz es un chat oscuro tipo WhatsApp optimizado para teléfono (PWA). Backend en Python/FastAPI, SQLite como BD, Docker para contenedores, Coolify para despliegue final desde GitHub.

**ESTADO:** Aplicacion funcionando correctamente en produccion. Explorador de archivos en sidebar con tabs (Conversaciones/Archivos) y arbol colapsable por tipo. Generacion de documentos soporta DOCX y TXT. Filtro backend de bloques `<think>` en streaming y en guardado/generacion. Documentos auto-regenerables si se pierden del disco tras redeploy.

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
