# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Secretaria — Asistente personal (secretaria) con chat continuo, gestion documental, generacion de documentos y reenvio por Telegram. Interfaz mobile-first (PWA) con tema oscuro tipo WhatsApp.

## Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite
- **Frontend:** HTML/CSS/JS vanilla, PWA (manifest + service worker)
- **Infra:** Docker, docker-compose, Coolify para deploy

## Build & Run

```bash
# Development (with hot reload via volume mounts)
docker compose up --build

# Access
http://localhost:8000
```

## Project Structure

```
backend/
  main.py          — FastAPI app entry point
  config.py        — Settings from env vars
  database.py      — SQLAlchemy engine + session
  models.py        — ORM models (User, Conversation, Message, File, TelegramContact, TelegramSend)
  auth.py          — JWT + bcrypt helpers, get_current_user dependency
  routers/         — API route modules (auth, chat, search, upload, documents, telegram)
  services/        — External API clients (minimax_ai, perplexity, telegram_bot, file_handler, doc_generator)
frontend/
  index.html       — SPA entry point
  css/style.css    — Dark theme, mobile-first
  js/app.js        — Auth, routing, core logic
  manifest.json    — PWA manifest
  sw.js            — Service worker
```

## API Endpoints

- `GET /health` — Health check
- `POST /api/auth/register` — Create account (username + password)
- `POST /api/auth/login` — Login, returns JWT
- All other `/api/*` endpoints require `Authorization: Bearer <token>`

## Environment Variables

See `.env.example` for the full list. Key variables:
- `JWT_SECRET` — Required for auth
- `MINIMAX_API_KEY` — For chat AI
- `PERPLEXITY_API_KEY` — For external search
- `TELEGRAM_BOT_TOKEN` — For Telegram forwarding

## Development Notes

- SQLite database stored at `/data/secretaria.db` inside Docker (persistent volume)
- Uploaded files stored in `/data/` subdirectories
- Frontend served as static files by FastAPI (mounted at `/`)
- The static mount must be the **last** route registered in main.py (it catches all unmatched paths)
