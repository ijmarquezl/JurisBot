# System Architecture: JurisBot

**Version:** 2.0 (SecWeb Refactor)
**Date:** 2025-12-26

## 1. Overview
JurisBot is a multi-tenant AI-powered legal assistant platform. It uses a Microservices-based architecture orchestrated by Docker Compose.

## 2. Core Components

### 2.1 Backend (`jurisbot-backend`)
- **Framework:** FastAPI (Python 3.11)
- **Architecture:** Clean Architecture (Domain-Driven Design inspired)
    - **Domain:** `app/domain` (Models, Ports, Schemas) - *Pure, no dependencies.*
    - **Application:** `app/application` (Services, Use Cases) - *Orchestration logic.*
    - **Infrastructure:** `app/infrastructure` (Adapters)
        - `web/`: FastAPI Routers (`routers/`), Main App.
        - `db/`: Database Adapters (MongoDB, PostgreSQL).
        - `ai/`: AI Agents (`graph_agent`, `scraper_agent`) and Tools.
        - `utils/`: Common utilities.
- **Port:** 8000

### 2.2 Scheduler (`jurisbot-scheduler`)
- **Function:** Runs background tasks (Legal Scraping, Document Processing).
- **Engine:** APScheduler (BlockingScheduler).
- **Dependencies:** Shares `infrastructure` code with Backend.

### 2.3 Databases
- **MongoDB:** Stores User, Tenant, and Project data.
    - Multi-tenant implementation (one DB per tenant or shared).
- **PostgreSQL (pgvector):** Stores Vector Embeddings for RAG.

### 2.4 AI Agents (Infrastructure Layer)
- **Graph Agent:** LangGraph-based conversational agent.
- **Scraper Agent:** Web scraping for legal documents (uses Browser Tools).
- **RAG Agent:** Retrieval-Augmented Generation for legal queries.

## 3. Directory Structure
```
jurisconsultor/
├── app/
│   ├── domain/         # Business Logic & Models
│   ├── application/    # Application Services
│   └── infrastructure/ # Frameworks & Drivers (Web, DB, AI)
├── scripts/            # Operational Scripts (Create Admin, Scrapers)
├── Dockerfile          # Backend Image Definition
└── docker-compose.yml  # Orchestration
```

## 4. Security & Standards (SecWeb 2.0)
- **Layered Isolation:** Infrastructure changes do not affect Domain models.
- **Environment config:** Sensitive data via `.env` and Docker secrets.
- **Audit Logging:** `AUDIT.md` tracks major risks and mitigations.
