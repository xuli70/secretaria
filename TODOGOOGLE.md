# TODOGOOGLE.md — Plan de Integracion Google Account

> **Proyecto:** Secretaria — Asistente Personal PWA
> **Objetivo:** Integrar Google Account (OAuth 2.0) para acceso a Calendar, Gmail, Drive y Contacts
> **Fecha creacion:** 2026-02-07
> **Estado global:** Fase 9+10 completadas (OAuth infraestructura + flujo completo)

---

## Resumen de fases

| Fase | Nombre | Estado |
|------|--------|--------|
| 9 | Seguridad de secretos Google + variables de entorno | Completada |
| 10 | OAuth 2.0 — Flujo de autenticacion Google | Completada |
| 11 | Google Calendar — Lectura y creacion de eventos | Pendiente |
| 12 | Gmail — Lectura y envio de correos | Pendiente |
| 13 | Google Drive — Explorar y subir archivos | Pendiente |
| 14 | Google Contacts — Lectura de contactos | Pendiente |
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

> **Estado:** [ ] Pendiente
> **Prioridad:** Alta

### Objetivo
Leer eventos del calendario del usuario y crear nuevos eventos desde el chat.

### Tareas
- [ ] Crear `backend/services/google_calendar.py`:
  - `list_events(token, time_min, time_max, max_results)` — listar eventos
  - `get_event(token, event_id)` — detalle de un evento
  - `create_event(token, summary, start, end, description?, location?, attendees?)` — crear evento
  - `delete_event(token, event_id)` — eliminar evento
- [ ] Crear endpoints en `backend/routers/google.py` (o sub-router):
  - `GET /api/google/calendar/events?from=&to=` — listar eventos en rango
  - `GET /api/google/calendar/events/today` — eventos de hoy
  - `GET /api/google/calendar/events/week` — eventos de la semana
  - `POST /api/google/calendar/events` — crear evento
  - `DELETE /api/google/calendar/events/{id}` — eliminar evento
- [ ] Frontend: vista de eventos en sidebar (tab o seccion)
- [ ] Frontend: renderizar eventos como cards (titulo, hora, ubicacion)
- [ ] Frontend: formulario basico de creacion de evento

### Verificacion
- [ ] `GET /api/google/calendar/events/today` → lista eventos de hoy
- [ ] `POST /api/google/calendar/events` → crea evento, aparece en Google Calendar
- [ ] Eventos renderizados correctamente en frontend
- [ ] Sin conexion Google → mensaje "Conecta tu cuenta Google"
- [ ] Zona horaria correcta en eventos creados

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 11 completada. Verificar que eventos creados desde la app aparecen correctamente en Google Calendar del usuario.

---

## Fase 12: Gmail — Lectura y envio de correos

> **Estado:** [ ] Pendiente
> **Prioridad:** Media

### Objetivo
Leer inbox del usuario y enviar correos desde el chat.

### Tareas
- [ ] Crear `backend/services/google_gmail.py`:
  - `list_messages(token, query, max_results)` — listar mensajes (inbox)
  - `get_message(token, message_id)` — detalle de un mensaje
  - `send_message(token, to, subject, body, cc?, bcc?)` — enviar correo
  - `list_labels(token)` — listar labels/carpetas
- [ ] Crear endpoints:
  - `GET /api/google/gmail/messages?q=&max=` — listar mensajes
  - `GET /api/google/gmail/messages/unread` — mensajes no leidos
  - `GET /api/google/gmail/messages/{id}` — detalle de mensaje
  - `POST /api/google/gmail/send` — enviar correo
- [ ] Frontend: vista de inbox en sidebar o modal
- [ ] Frontend: renderizar emails como cards (remitente, asunto, snippet, fecha)
- [ ] Frontend: formulario de envio de correo (to, subject, body)
- [ ] Frontend: indicador de correos no leidos

### Verificacion
- [ ] `GET /api/google/gmail/messages/unread` → lista emails no leidos
- [ ] `GET /api/google/gmail/messages/{id}` → contenido completo del email
- [ ] `POST /api/google/gmail/send` → correo enviado, aparece en Sent de Gmail
- [ ] Emails renderizados correctamente en frontend
- [ ] Sin conexion Google → mensaje amigable

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 12 completada. Probar envio de correo en produccion y verificar que llega al destinatario.

---

## Fase 13: Google Drive — Explorar y subir archivos

> **Estado:** [ ] Pendiente
> **Prioridad:** Media

### Objetivo
Explorar archivos del Drive del usuario y subir archivos desde el chat.

### Tareas
- [ ] Crear `backend/services/google_drive.py`:
  - `list_files(token, query, folder_id, max_results)` — listar archivos
  - `get_file(token, file_id)` — metadata de archivo
  - `download_file(token, file_id)` — descargar contenido
  - `upload_file(token, filename, content, mime_type, folder_id?)` — subir archivo
  - `list_folders(token)` — listar carpetas
- [ ] Crear endpoints:
  - `GET /api/google/drive/files?q=&folder=` — listar archivos
  - `GET /api/google/drive/files/recent` — archivos recientes
  - `GET /api/google/drive/files/{id}` — metadata
  - `GET /api/google/drive/files/{id}/download` — descargar
  - `POST /api/google/drive/upload` — subir archivo
- [ ] Frontend: explorador Drive en sidebar (integrar con tab Archivos existente?)
- [ ] Frontend: renderizar archivos Drive como cards (nombre, tipo, tamano, fecha)
- [ ] Frontend: boton "Subir a Drive" en archivos generados/subidos

### Verificacion
- [ ] `GET /api/google/drive/files/recent` → lista archivos recientes
- [ ] `POST /api/google/drive/upload` → archivo visible en Google Drive del usuario
- [ ] Descargar archivo desde Drive → descarga correcta
- [ ] Subir documento generado a Drive → aparece en Drive
- [ ] Frontend muestra archivos Drive correctamente

> **Post-push:** Actualizar SEGUIMIENTO.md con Fase 13 completada. Verificar que archivos subidos aparecen en Google Drive del usuario.

---

## Fase 14: Google Contacts — Lectura de contactos

> **Estado:** [ ] Pendiente
> **Prioridad:** Baja

### Objetivo
Leer contactos de Google del usuario para autocompletar destinatarios en Gmail y Calendar.

### Tareas
- [ ] Crear `backend/services/google_contacts.py`:
  - `list_contacts(token, query, max_results)` — listar contactos
  - `get_contact(token, contact_id)` — detalle de contacto
  - `search_contacts(token, query)` — buscar por nombre/email
- [ ] Crear endpoints:
  - `GET /api/google/contacts?q=&max=` — listar/buscar contactos
  - `GET /api/google/contacts/{id}` — detalle
- [ ] Frontend: autocompletar contactos Google al escribir destinatario en Gmail
- [ ] Frontend: sugerir asistentes de Calendar desde contactos Google

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
