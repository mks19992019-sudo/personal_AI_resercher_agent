# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal AI chatbot using LangGraph for agent orchestration, FastAPI for the backend API, and PostgreSQL for state persistence via a LangGraph checkpointer. A standalone Python HTTP server in `ui/` serves the chat frontend.

## Development Commands

### Backend (FastAPI)
```bash
uvicorn main:app --reload
```
The API runs at `http://127.0.0.1:8000`. The `/chat` endpoint accepts POST requests with `user` and `thread_id` fields.

### UI Server
```bash
python ui/server.py
```
Runs at `http://127.0.0.1:3000` and proxies chat requests to the FastAPI backend at `/chat`. Configure with `BACKEND_URL` env var if needed.

### Database (PostgreSQL)
```bash
docker compose up
```
Starts postgres on port `5442`. Connection URI: `postgresql://postgres:postgres@localhost:5442/postgres`.

## Architecture

### State Graph (`graph.py`)
The `work_flow` is a LangGraph `StateGraph` with two nodes:
- `AI_agent`: Invokes the ChatGroq react agent with conversation history (and summary if present)
- `summery`: Condensed summary of conversation when message count exceeds 6

Transitions: `START` → `AI_agent` → conditional (summery if >6 messages, else END).

The `Chatstate` extends `MessagesState` with a `summary: str` field.

Checkpoints are persisted to PostgreSQL via `PostgresSaver` using a connection pool.

### API (`main.py`)
FastAPI app with a single `/chat` POST endpoint. Takes `user` and `thread_id` (both aliased from common variants), builds initial `MessagesState`, invokes the graph with the thread_id as config, returns the last message content.

### UI (`ui/`)
- `server.py`: `ThreadingHTTPServer` with `SimpleHTTPRequestHandler` — serves static files and proxies `/api/chat` POST requests to the FastAPI backend
- `index.html` + `app.js` + `styles.css`: Vanilla JS chat interface

## Key Dependencies
- **langgraph** + **langgraph-checkpoint-postgres**: Agent workflow and PostgreSQL state persistence
- **langchain-groq**: ChatGroq LLM integration
- **fastapi** + **uvicorn**: REST API server
- **psycopg_pool**: PostgreSQL connection pooling for the checkpointer
- **python-dotenv**: Environment variable loading from `.env`

## Environment Variables
- `GROQ_API_KEY`: Required for ChatGroq LLM access
- `DB_URI`: PostgreSQL connection string (defaults to `postgresql://postgres:postgres@localhost:5442/postgres`)
- `UI_HOST`, `UI_PORT`, `BACKEND_URL`, `BACKEND_TIMEOUT_SECONDS`: UI server configuration