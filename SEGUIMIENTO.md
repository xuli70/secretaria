# SEGUIMIENTO - Secretaria

> **Objetivo:** Aplicación web mobile-first de asistente personal (secretaria) con chat continuo, gestión documental, generación de documentos y reenvío por Telegram
> **Carpeta:** D:\MINIMAX\Secretaria
> **Ultima actualizacion:** 2026-02-06 19:45
> **Estado global:** Fase 0 de 6 (completada)

---

## Resumen ejecutivo

Proyecto nuevo. Se ha definido la arquitectura, el stack técnico y las 7 fases de desarrollo. El cerebro es MINIMAX AI (chat) + Perplexity (búsqueda externa). La interfaz es un chat oscuro tipo WhatsApp optimizado para teléfono (PWA). Backend en Python/FastAPI, SQLite como BD, Docker para contenedores, Coolify para despliegue final desde GitHub.

**PROXIMO PASO:** Iniciar Fase 1: Chat central con MINIMAX AI, burbujas de chat, historial persistente.

---

## Bloqueos activos

> **Sin bloqueos activos**

---

## Decisiones de diseño tomadas

| Decision | Resultado | Fecha |
|----------|-----------|-------|
| Autenticación | Login completo (usuario + contraseña, JWT) | 2026-02-06 |
| Estilo UI | Tema oscuro tipo WhatsApp, burbujas de chat | 2026-02-06 |
| API Keys | En variables de entorno Coolify, inyectadas al redeploy desde GitHub | 2026-02-06 |
| Despliegue | Desarrollo local Docker primero → Coolify cuando esté listo | 2026-02-06 |
| Stack backend | Python 3.11 + FastAPI + SQLAlchemy + SQLite | 2026-02-06 |
| Stack frontend | HTML/CSS/JS vanilla, PWA (manifest + service worker) | 2026-02-06 |

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

> **Estado:** [ ] Pendiente
> **Prioridad:** Alta

---

## Fase 2: Entrada Multimodal + Almacen

> **Estado:** [ ] Pendiente
> **Prioridad:** Alta

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

## Registro de sesiones

| Sesion | Fecha | Fase trabajada | Avances | Siguiente paso |
|--------|-------|----------------|---------|----------------|
| 1 | 2026-02-06 | Planificacion | Definido objetivo, arquitectura, stack, 7 fases | Iniciar Fase 0: scaffolding |
| 2 | 2026-02-06 | Fase 0 | Fase 0 completada: scaffolding, auth, Docker verificado, Git init | Iniciar Fase 1: Chat + MINIMAX AI |
