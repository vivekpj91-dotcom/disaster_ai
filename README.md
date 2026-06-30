# DisasterAssist AI

**A mobile-first emergency response assistant that coordinates triage, shelters, hospitals, damage assessment, weather alerts, and preparedness guidance through a multi-agent AI backend.**

DisasterAssist AI is built for the first chaotic minutes of a disaster, when people need fast, calm, location-aware help. It combines a professional Streamlit mobile interface, a FastAPI gateway, Google ADK multi-agent orchestration, SQLite-backed emergency resource data, and an MCP tool server for structured safety lookups.

## Why It Matters

During floods, earthquakes, wildfires, cyclones, and heatwaves, people often ask several urgent questions at once:

- Am I in danger right now?
- Where is the nearest shelter?
- Which hospital can handle injuries?
- Is this building or road damage dangerous?
- What should my family pack or do next?

DisasterAssist AI turns those scattered needs into coordinated specialist workflows. A planner agent routes each request to the right worker agent, then the backend returns a practical response through a mobile-style dashboard.

## Highlights

- **Multi-agent architecture:** planner coordinator plus specialist agents for triage, hospitals, shelters, resources, weather, damage, information, and checklists.
- **Mobile-first UI:** professional white/blue emergency operations interface with red reserved for active alerts and emergency actions.
- **Backend-connected dashboard:** live backend status checks, JWT login, chat, emergency dispatch, damage image upload, and location-aware requests.
- **Resilient demo mode:** works without a Gemini API key by returning deterministic fallback responses, so the demo remains reliable offline.
- **Safety-conscious backend:** rate limiting, prompt-injection filtering, JWT auth, image magic-number validation, upload size checks, and global exception handling.
- **MCP-ready tools:** separate FastMCP service exposes structured search for shelters, hospitals, disaster guidelines, first aid, and manuals.
- **Dockerized stack:** backend, frontend, and MCP server can run together with Docker Compose.

## System Architecture

```text
User / Judge
    |
    v
Streamlit Mobile UI
    |  API_BASE_URL
    v
FastAPI Backend Gateway
    |        |        |
    |        |        +--> SQLite resource database
    |        |
    |        +--> Image validation and damage assessment
    |
    +--> Google ADK Planner Agent
             |
             +--> Triage Worker
             +--> Shelter Worker
             +--> Hospital Worker
             +--> Resource Worker
             +--> Weather Worker
             +--> Damage Worker
             +--> Checklist Worker
             +--> Info Worker

FastMCP Server
    |
    +--> Shelter, hospital, first-aid, and guideline tools
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Streamlit, Pandas |
| Backend | FastAPI, Pydantic, PyJWT |
| Agents | Google ADK, Gemini-ready worker agents |
| Tools | FastMCP |
| Database | SQLite, SQLAlchemy |
| Deployment | Docker, Docker Compose |
| Security | Rate limiting, JWT, input filtering, upload validation |

## Core Features

### Emergency Triage

Users can submit urgent rescue or hazard reports with phone number, GPS coordinates, and incident details. The system flags critical emergency language and returns immediate action guidance.

### Shelter And Hospital Guidance

Seeded emergency resource data supports nearby shelter and medical facility lookup. Distance calculations use Haversine geospatial logic.

### AI Chat Assistant

The chat interface sends user messages and coordinates to the FastAPI backend. The planner agent can route requests to specialized workers, while demo fallback keeps responses available without external API access.

### Damage Assessment Uploads

Users can upload JPG or PNG photos. The backend validates file type and content headers, checks size limits, saves the upload, and returns a structured hazard assessment.

### Preparedness Checklist Builder

The checklist workflow personalizes emergency kit suggestions based on hazard type, household size, pets, and children.

### Backend Health Visibility

The UI shows whether the FastAPI backend is online

## Project Structure

```text
agents/        Google ADK planner and specialist worker agents
backend/       FastAPI gateway, auth, schemas, security, routes
config/        Environment-driven application settings
database/      SQLAlchemy models, DB connection, seed data
docker/        Dockerfiles for backend, frontend, and MCP services
frontend/      Streamlit professional mobile UI
mcp_server/    FastMCP emergency lookup tools
tools/         Shared geospatial and image utilities
```

## Quick Start

### 1. Create Environment

```powershell
cd C:\Users\vivek\disaster-assist-ai
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
copy .env.example .env
```

Set these values in `.env`:

```text
JWT_SECRET=replace_with_a_long_random_secret
DEMO_USER_EMAIL=user@example.com
DEMO_USER_PASSWORD=password123
DATABASE_URL=sqlite:///./database/database.db
API_BASE_URL=http://localhost:8000/api
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

`GOOGLE_API_KEY` is optional. If it is empty, the app runs in deterministic demo mode.

### 3. Initialize Database

```powershell
python -m database.init_db
```

### 4. Start Backend

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Frontend

Open a second terminal:

```powershell
cd C:\Users\vivek\disaster-assist-ai
.\venv\Scripts\activate
streamlit run frontend/main.py
```

Open:

```text
http://localhost:8501
```

Backend docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/health
```

## Docker Run

```powershell
docker compose up --build
```

Services:

- Streamlit UI: `http://localhost:8501`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Demo Flow

1. Open the Streamlit UI.
2. Confirm the header says `Backend online`.
3. Go to **Chat** and ask: `Where is the nearest shelter?`
4. Go to **Alert** and submit a critical emergency message.
5. Go to **Scan** and upload a JPG or PNG damage image.
6. Go to **Kit** and generate a preparedness checklist.

## Demo Login

The demo login is environment-driven:

```text
DEMO_USER_EMAIL=user@example.com
DEMO_USER_PASSWORD=password123
```

These are not hardcoded secrets in the backend. Change them before any public deployment.

## API Keys And Secrets

No real API keys are committed in this project.

- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- `GOOGLE_API_KEY` is optional for demo mode.
- `JWT_SECRET` should be set in `.env` or the deployment environment.

## Security And Safety Notes

This is a competition prototype, not a replacement for official emergency services.

Implemented safeguards:

- JWT authentication for personalized flows
- anonymous access for emergency usability
- request rate limiting
- basic prompt-injection filtering
- secure image extension and magic-byte checks
- 10 MB upload limit
- global exception handler to avoid raw stack traces
- environment-based secrets

Production hardening roadmap:

- replace demo auth with OAuth or verified identity provider
- use Redis-backed distributed rate limiting
- use PostGIS or a managed geospatial database
- connect to official live emergency feeds
- store images in cloud object storage
- add audit trails and responder dashboards

## Competition Positioning

DisasterAssist AI demonstrates how agentic AI can support emergency decision-making without pretending to replace authorities. The system focuses on clear triage, resource discovery, hazard interpretation, and preparedness guidance through a deployable full-stack prototype.


 THANKYOU :)
