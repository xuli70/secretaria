# TODOGOOGLE.md — Plan de Integracion Google Account

> **Proyecto:** Secretaria — Asistente Personal PWA
> **Objetivo:** Integrar Google Account (OAuth 2.0) para acceso a Calendar, Gmail, Drive y Contacts
> **Fecha creacion:** 2026-02-07
> **Estado global:** Fase 9+10+11+12+13+14 completadas (OAuth + Calendar + Gmail + Drive + Contacts)

---

## Resumen de fases

| Fase | Nombre | Estado |
|------|--------|--------|
| 9 | Seguridad de secretos Google + variables de entorno | Completada |
| 10 | OAuth 2.0 — Flujo de autenticacion Google | Completada |
| 11 | Google Calendar — Lectura y creacion de eventos | Completada |
| 12 | Gmail — Lectura y envio de correos | Completada |
| 13 | Google Drive — Explorar y subir archivos | Completada |
| 14 | Google Contacts — Lectura de contactos | Completada |
| 15 | Comandos naturales — Chat con acciones Google | Pendiente |
| 16 | UI integrada — Panel Google en sidebar | Pendiente |

---

## Fase 9: Seguridad de secretos Google + variables de entorno

> **Estado:** [x] Completada
> **Prioridad:** Alta (prerequisito de todo lo demas)

### Objetivo
Preparar la infraestructura de configuracion para las credenciales OAuth de Google, garantizando que ningun secreto se commitee al repositorio.

### Tareas
- [x] Agregar variables a `backend/config.py`: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GOOGLE_TOKEN_ENCRYPTION_KEY
- [x] Agregar variables a `.env.example` solo con nombres, sin valores reales
- [x] Crear modelo `GoogleToken` en `models.py` (id, user_id FK, encrypted_token LargeBinary, scopes Text, timestamps)
- [x] Agregar `cryptography` a `requirements.txt`
- [x] Crear `backend/services/google_auth.py` (encrypt/decrypt/store/get/delete tokens con Fernet)
- [x] Relacion `google_token` agregada en modelo User (uselist=False)
- [x] Import `LargeBinary` agregado a models.py

### Archivos creados/modificados
- `backend/config.py` — 4 variables Google OAuth
- `.env.example` — Seccion Google OAuth (solo placeholders)
- `backend/models.py` — Import LargeBinary, modelo GoogleToken, relacion en User
- `backend/services/google_auth.py` — CREADO: _get_fernet, encrypt_token, decrypt_token, get_stored_token, store_token, delete_token
- `requirements.txt` — Agregado cryptography

---

## Fase 10: OAuth 2.0 — Flujo de autenticacion Google

> **Estado:** [x] Completada
> **Prioridad:** Alta (prerequisito para todas las APIs Google)

### Objetivo
Implementar el flujo completo OAuth 2.0 con Google para obtener y refrescar tokens de acceso.

### Tareas
- [x] Instalar google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client en requirements.txt
- [x] Crear `backend/routers/google.py` con 4 endpoints:
  - `GET /api/google/status` — estado de conexion (connected, scopes)
  - `GET /api/google/auth-url` — genera URL de consentimiento Google con state=user_{id}
  - `GET /api/google/callback` — intercambia code por tokens, cifra y guarda, redirige a app
  - `POST /api/google/disconnect` — revoca token (best-effort), elimina de BD
- [x] Helper `get_valid_credentials()` — devuelve creds validas, refresca si expiro (exportada para fases futuras)
- [x] Scopes: calendar, gmail.modify, drive, contacts.readonly
- [x] OAuth params: access_type="offline", prompt="consent" (fuerza refresh_token)
- [x] Registrar google_router en main.py (antes del static mount)
- [x] Frontend: boton Google en header (icono G, azul → verde cuando conectado)
- [x] Frontend: modal Google (bottom-sheet, boton conectar, scopes como badges, boton desconectar)
- [x] Frontend: deteccion de ?google_connected=true / ?google_error= en URL → toast + limpiar URL
- [x] Frontend: checkGoogleStatus() al enterApp, reset al logout

### Verificacion
- [ ] Click boton Google en header → abre modal con "Conectar Google"
- [ ] Click "Conectar Google" → redirige a pantalla de consentimiento Google
- [ ] Autorizar → redirect a callback → token cifrado en BD → redirect a app con toast
- [ ] `GET /api/google/status` → `{connected: true, scopes: [...]}`
- [ ] Modal muestra scopes (Calendar, Gmail, Drive, Contacts) y boton "Desconectar"
- [ ] Click "Desconectar" → token eliminado, UI actualiza
- [ ] Boton Google cambia color (azul → verde cuando conectado)

### Archivos creados/modificados
- `requirements.txt` — Agregados google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client
- `backend/routers/google.py` — CREADO: 4 endpoints OAuth, _build_flow, _credentials_to_dict, _dict_to_credentials, get_valid_credentials
- `backend/main.py` — Import y registro google_router
- `frontend/index.html` — Boton Google en header (SVG), modal Google (overlay + modal con conectar/desconectar/scopes)
- `frontend/css/style.css` — Estilos btn-google, google-overlay, google-modal, google-modal-header, google-status-badge, btn-google-connect, btn-google-disconnect, google-scope-item
- `frontend/js/app.js` — Estado googleConnected, DOM refs, openGoogleModal/closeGoogleModal, checkGoogleStatus, updateGoogleUI, SCOPE_LABELS, OAuth redirect handling, enterApp integration, logout reset

---

## Fase 11: Google Calendar — Lectura y creacion de eventos

> **Estado:** [x] Completada
> **Prioridad:** Alta

### Objetivo
Leer eventos del calendario del usuario y crear nuevos eventos desde el chat.

### Tareas
- [x] Crear `backend/services/google_calendar.py`:
  - `list_events(creds, time_min, time_max, max_results)` — listar eventos
  - `get_event(creds, event_id)` — detalle de un evento
  - `create_event(creds, summary, start, end, description?, location?, attendees?)` — crear evento
  - `delete_event(creds, event_id)` — eliminar evento
- [x] Crear endpoints en `backend/routers/google.py`:
  - `GET /api/google/calendar/events?time_min=&time_max=&max_results=` — listar eventos en rango
  - `GET /api/google/calendar/events/today` — eventos de hoy
  - `GET /api/google/calendar/events/week` — eventos de la semana
  - `POST /api/google/calendar/events` — crear evento (body: summary, start, end, description?, location?, attendees?)
  - `DELETE /api/google/calendar/events/{event_id}` — eliminar evento
- [x] Frontend: seccion Calendar dentro del modal Google (tabs Hoy/Semana)
- [x] Frontend: renderizar eventos como cards (hora, titulo, ubicacion, boton eliminar)
- [x] Frontend: formulario basico de creacion de evento (titulo, inicio, fin, ubicacion, descripcion)
- [x] Frontend: click en titulo de evento → abre link en Google Calendar

### Archivos creados/modificados
- `backend/services/google_calendar.py` — CREADO: _get_service, list_events, get_event, create_event, delete_event, _parse_datetime, _format_event
- `backend/routers/google.py` — Agregados 5 endpoints calendar, CreateEventBody model, _require_google helper
- `frontend/index.html` — Seccion Calendar en google-connected: gcal-events, gcal-form con inputs
- `frontend/css/style.css` — Estilos gcal-section, gcal-header, gcal-tabs, gcal-event, gcal-form, btn-gcal-*
- `frontend/js/app.js` — loadCalendarEvents, renderCalendarEvents, formatCalendarTime, toLocalISOString, gcalTabs, gcalForm handlers

### Verificacion
- [ ] `GET /api/google/calendar/events/today` → lista eventos de hoy
- [ ] `POST /api/google/calendar/events` → crea evento, aparece en Google Calendar
- [ ] Eventos renderizados correctamente en frontend
- [ ] Sin conexion Google → mensaje "Conecta tu cuenta Google"
- [ ] Zona horaria correcta en eventos creados

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 11 completada. Verificar que eventos creados desde la app aparecen correctamente en Google Calendar del usuario.

---

## Fase 12: Gmail — Lectura y envio de correos

> **Estado:** [x] Completada
> **Prioridad:** Media

### Objetivo
Leer inbox del usuario y enviar correos desde el chat.

### Tareas
- [x] Crear `backend/services/google_gmail.py`:
  - `list_messages(creds, query, max_results)` — listar mensajes (inbox)
  - `get_message(creds, message_id)` — detalle de un mensaje
  - `send_message(creds, to, subject, body, cc?, bcc?)` — enviar correo
- [x] Crear endpoints:
  - `GET /api/google/gmail/messages?q=&max=` — listar mensajes
  - `GET /api/google/gmail/messages/unread` — mensajes no leidos
  - `GET /api/google/gmail/messages/{id}` — detalle de mensaje
  - `POST /api/google/gmail/send` — enviar correo
- [x] Frontend: seccion Gmail dentro del modal Google (tabs Inbox/No leidos)
- [x] Frontend: renderizar emails como cards (remitente, asunto, snippet, fecha)
- [x] Frontend: formulario de envio de correo (to, subject, body)
- [x] Frontend: indicador de correos no leidos (badge rojo)
- [x] Frontend: vista detalle de email (click en card abre body completo)

### Archivos creados/modificados
- `backend/services/google_gmail.py` — CREADO: _get_service, list_messages, get_message, send_message, _get_header, _format_message_summary, _format_message_full, _extract_body
- `backend/routers/google.py` — Agregados 4 endpoints Gmail, SendEmailBody model, import google_gmail
- `frontend/index.html` — Seccion Gmail en google-connected: gmail-messages, gmail-compose form, gmail-detail view
- `frontend/css/style.css` — Estilos gmail-section, gmail-header, gmail-tabs, gmail-msg, gmail-compose, gmail-detail, gmail-unread-badge, btn-gmail-*
- `frontend/js/app.js` — loadGmailMessages, renderGmailMessages, formatGmailDate, openGmailDetail, gmailTabs, gmailCompose handlers, btnGmailSend

### Verificacion
- [ ] `GET /api/google/gmail/messages/unread` → lista emails no leidos
- [ ] `GET /api/google/gmail/messages/{id}` → contenido completo del email
- [ ] `POST /api/google/gmail/send` → correo enviado, aparece en Sent de Gmail
- [ ] Emails renderizados correctamente en frontend
- [ ] Sin conexion Google → mensaje amigable

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 12 completada. Probar envio de correo en produccion y verificar que llega al destinatario.

---

## Fase 13: Google Drive — Explorar y subir archivos

> **Estado:** [x] Completada
> **Prioridad:** Media

### Objetivo
Explorar archivos del Drive del usuario y subir archivos desde el chat.

### Tareas
- [x] Crear `backend/services/google_drive.py`:
  - `list_files(creds, query, folder_id, max_results)` — listar archivos
  - `list_recent(creds, max_results)` — archivos recientes
  - `get_file(creds, file_id)` — metadata de archivo
  - `download_file(creds, file_id)` — descargar contenido (con export para Google Docs)
  - `upload_file(creds, filename, content, mime_type, folder_id?)` — subir archivo
  - `list_folders(creds)` — listar carpetas
- [x] Crear endpoints:
  - `GET /api/google/drive/files?q=&folder=&max=` — listar archivos
  - `GET /api/google/drive/files/recent` — archivos recientes
  - `GET /api/google/drive/files/{id}` — metadata
  - `GET /api/google/drive/files/{id}/download` — descargar
  - `POST /api/google/drive/upload` — subir archivo
- [x] Frontend: seccion Drive dentro del modal Google (tabs Recientes/Buscar)
- [x] Frontend: renderizar archivos Drive como cards (nombre, tipo, tamano, fecha, icono por tipo)
- [x] Frontend: boton subir archivo a Drive (form con file picker)
- [x] Frontend: busqueda en Drive (search bar con input + boton)
- [x] Frontend: click en archivo → abre en Google Drive (webViewLink)
- [x] Frontend: boton descargar en cada archivo (con export para Google Workspace files)

### Archivos creados/modificados
- `backend/services/google_drive.py` — CREADO: _get_service, list_files, list_recent, get_file, download_file, upload_file, list_folders, _format_file, MIME_ICONS
- `backend/routers/google.py` — Agregados 5 endpoints Drive, imports drive_*, UploadFile, File, Response
- `frontend/index.html` — Seccion Drive en google-connected: gdrive-files, gdrive-search-bar, gdrive-upload-form
- `frontend/css/style.css` — Estilos gdrive-section, gdrive-header, gdrive-tabs, gdrive-file, gdrive-upload-form, btn-gdrive-*
- `frontend/js/app.js` — loadDriveFiles, renderDriveFiles, formatDriveDate, gdriveTabs, gdriveUpload handlers

### Verificacion
- [ ] `GET /api/google/drive/files/recent` → lista archivos recientes
- [ ] `POST /api/google/drive/upload` → archivo visible en Google Drive del usuario
- [ ] Descargar archivo desde Drive → descarga correcta
- [ ] Subir documento generado a Drive → aparece en Drive
- [ ] Frontend muestra archivos Drive correctamente

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 13 completada. Verificar que archivos subidos aparecen en Google Drive del usuario.

---

## Fase 14: Google Contacts — Lectura de contactos

> **Estado:** [x] Completada
> **Prioridad:** Baja

### Objetivo
Leer contactos de Google del usuario para autocompletar destinatarios en Gmail y Calendar.

### Tareas
- [x] Crear `backend/services/google_contacts.py`:
  - `list_contacts(creds, query, max_results)` — listar contactos
  - `get_contact(creds, resource_name)` — detalle de contacto
  - `search_contacts(creds, query)` — buscar por nombre/email
- [x] Crear endpoints:
  - `GET /api/google/contacts?q=&max=` — listar/buscar contactos
  - `GET /api/google/contacts/search?q=&max=` — buscar contactos (People API searchContacts)
  - `GET /api/google/contacts/{id}` — detalle
- [x] Frontend: autocompletar contactos Google al escribir destinatario en Gmail
- [x] Frontend: contactos pre-cargados al conectar Google, con busqueda remota como fallback

### Archivos creados/modificados
- `backend/services/google_contacts.py` — CREADO: _get_service, list_contacts, search_contacts, get_contact, _has_email, _format_contact
- `backend/routers/google.py` — Agregados 3 endpoints Contacts, imports google_contacts
- `frontend/index.html` — Wrapper contact-autocomplete-wrapper en gmail-to input, dropdown container
- `frontend/css/style.css` — Estilos contact-autocomplete, contact-ac-item, contact-ac-avatar, contact-ac-info
- `frontend/js/app.js` — contactsCache, loadContactsCache, filterContacts, searchContactsRemote, renderACResults, setupContactAutocomplete, keyboard nav, reset on disconnect/logout

### Verificacion
- [ ] `GET /api/google/contacts` → lista contactos del usuario
- [ ] Buscar contacto por nombre → resultados correctos
- [ ] Autocompletar en formulario Gmail → sugiere contactos Google
- [ ] Sin conexion Google → autocompletar deshabilitado silenciosamente

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 14 completada.

---

## Fase 15: Comandos naturales — Chat con acciones Google

> **Estado:** [ ] Pendiente
> **Prioridad:** Media

### Objetivo
Permitir que el usuario use lenguaje natural en el chat para interactuar con servicios Google. La IA interpreta la intencion y ejecuta la accion correspondiente.

### Tareas
- [ ] Crear `backend/services/google_actions.py`:
  - Parser de intenciones: detectar si el mensaje del usuario pide una accion Google
  - Acciones soportadas:
    - "Agenda una reunion con X manana a las 3pm" → `create_event`
    - "Que tengo hoy en el calendario?" → `list_events today`
    - "Envia un correo a X diciendo Y" → `send_message`
    - "Muestrame mis correos no leidos" → `list_messages unread`
    - "Sube este documento a Drive" → `upload_file`
  - Usar function calling de MiniMax o prompt engineering con JSON schema
- [ ] Modificar `backend/routers/chat.py`:
  - Detectar intencion Google en el mensaje
  - Ejecutar accion Google si aplica
  - Incluir resultado en la respuesta del chat
- [ ] Frontend: renderizar resultados de acciones Google inline en burbujas
  - Eventos creados → card con link a Calendar
  - Correos enviados → confirmacion con destinatario
  - Archivos subidos → card con link a Drive

### Verificacion
- [ ] "Que tengo manana?" → lista eventos de manana en burbuja
- [ ] "Agenda reunion con Juan a las 4pm" → crea evento, confirma en burbuja
- [ ] "Envia correo a juan@email.com: Hola Juan" → envia correo, confirma
- [ ] "Mis correos no leidos" → lista ultimos emails no leidos
- [ ] Mensaje sin intencion Google → chat normal sin cambios
- [ ] Sin conexion Google → mensaje "Conecta tu cuenta Google para usar esta funcion"

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 15 completada. Probar los 5 tipos de comandos naturales en produccion.

---

## Fase 16: UI integrada — Panel Google en sidebar

> **Estado:** [ ] Pendiente
> **Prioridad:** Baja

### Objetivo
Panel unificado en el sidebar que muestre resumen de Calendar, Gmail y Drive del usuario.

### Tareas
- [ ] Agregar tab "Google" al sidebar (junto a Conversaciones y Archivos)
- [ ] Seccion Calendar:
  - Proximos 5 eventos
  - Boton "Ver todos" → lista completa
  - Boton "+" → crear evento rapido
- [ ] Seccion Gmail:
  - Ultimos 5 correos no leidos (badge con conteo)
  - Click en correo → detalle en modal
  - Boton "Componer" → formulario de envio
- [ ] Seccion Drive:
  - Archivos recientes (5)
  - Boton "Explorar" → navegacion de carpetas
  - Drag & drop para subir
- [ ] Indicador de conexion Google en header (icono Google, verde/gris)
- [ ] Auto-refresh cada 5 minutos (polling o timer)

### Verificacion
- [ ] Tab "Google" muestra las 3 secciones con datos reales
- [ ] Datos se actualizan al cambiar de tab
- [ ] Badge de correos no leidos se actualiza
- [ ] Crear evento desde sidebar → aparece en Calendar
- [ ] Sin conexion Google → tab muestra boton "Conectar"
- [ ] Mobile: sidebar con 3 tabs funciona correctamente

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 16 completada. Verificar rendimiento del sidebar con datos reales (no deberia tardar mas de 2s en cargar).

---

## Notas generales

### Dependencias nuevas (requirements.txt)
```
cryptography          # Fernet encryption para tokens OAuth
google-auth           # Google OAuth 2.0
google-auth-oauthlib  # OAuth flow helpers
google-auth-httplib2  # HTTP transport
google-api-python-client  # Google APIs (Calendar, Gmail, Drive, People)
```

### Variables de entorno nuevas (.env.example)
```
# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/google/callback
GOOGLE_TOKEN_ENCRYPTION_KEY=
```

### Modelo de datos nuevo (models.py)
```
GoogleToken:
  id              INTEGER PK
  user_id         INTEGER FK → User
  encrypted_token BLOB (Fernet-encrypted JSON)
  scopes          TEXT
  created_at      DATETIME
  updated_at      DATETIME
```

### Orden de implementacion recomendado
1. **Fase 9** → Seguridad primero (variables, cifrado, modelo BD)
2. **Fase 10** → OAuth flow (sin esto nada funciona)
3. **Fase 11** → Calendar (caso de uso mas natural para un asistente)
4. **Fase 12** → Gmail (segundo caso de uso mas pedido)
5. **Fase 13** → Drive (complementa archivos existentes)
6. **Fase 14** → Contacts (complementa Gmail y Calendar)
7. **Fase 15** → Comandos naturales (la magia del asistente)
8. **Fase 16** → UI panel (polish final)

### Seguridad — Resumen
- `.env` en `.gitignore` → secretos nunca commiteados
- `.env.example` solo con nombres de variables (plantilla)
- Produccion: variables en **Coolify UI** (Environment Variables)
- Tokens OAuth cifrados con **Fernet** (`GOOGLE_TOKEN_ENCRYPTION_KEY`) antes de SQLite
- `GOOGLE_TOKEN_ENCRYPTION_KEY` solo en `.env` local y Coolify — jamas en repositorio
- Refresh tokens almacenados cifrados; access tokens efimeros
- Scopes minimos necesarios por servicio
- Revocacion de tokens al desconectar cuenta Google
