# PIIShield

> **India-aware, Fail-Closed PII Protection Gateway for LLMs**

---

## 1. Project Overview

**PIIShield** is a high-security reverse proxy gateway designed to protect Personally Identifiable Information (PII) before requests reach third-party Large Language Models (LLMs). Built specifically with India-aware entity validation (including Aadhaar Verhoeff checksums and PAN structure validation), PIIShield provides symmetric request sanitization, reversible pseudonymization, strict fail-closed enforcement, and response de-pseudonymization.

> **Status Notice:** This project is currently in the foundational scaffolding stage. Core business logic (detection engines, policy execution, pseudonymization vaults, response scanning, and evaluation benchmarks) is intentionally staged for hands-on, modular implementation.

---

## 2. Architecture Overview

```
Client App
   │
   ▼
[ 1. FastAPI Gateway & Auth ] (API key / client_id scoping, rate limiting)
   │
   ▼
[ 2. Normalization & Offsets ] (NFC + whitespace collapse; 3-layer offset mapping)
   │
   ▼
[ 3. Hybrid Detection Engine ] 
     ├── Tier 1: Validated Regex + Checksum (Aadhaar Verhoeff, PAN structural)
     ├── Tier 2: High-confidence structured recognizers (Phone, Email)
     ├── Tier 3: General Presidio pattern recognizers
     └── Tier 4: Statistical NER (spaCy / Presidio NER)
   │
   ▼
[ 4. Consolidation & Precedence ] (Deterministic tie-breaking; ChromaDB for same-tier ties)
   │
   ▼
[ 5. Policy Engine ] (Deny-by-default, policy versioning, rules: BLOCK, MASK, PSEUDONYMIZE, ALLOW)
   │
   ▼
[ 6. Pseudonymization & Isolation ] (Reserved tokens e.g. ⟦PII_PERSON_01⟧, AES-encrypted pseudonym_lookup)
   │
   ▼
[ 7. External LLM Request ] ─── TRUST BOUNDARY ───► [ Third-Party LLM ]
   │                                                         │
   ▼                                                         ▼
[ 8. Response Scanning & Classification ] ◄─────────────────┘
     ├── Reflected Pseudonym (validated against active session lookup)
     ├── Reflected Original (ALLOWED vs UNEXPECTED)
     ├── Newly Generated PII
     └── Pattern-shaped Hallucinated PII
   │
   ▼
[ 9. Response Policy & De-pseudonymization ] (Restore valid pseudonyms last)
   │
   ▼
Client Response
```

---

## 3. Technology Stack

* **API Gateway & Backend:** FastAPI, Uvicorn, Pydantic
* **Database & Persistence:** PostgreSQL, SQLAlchemy, Alembic
* **PII Detection & NLP:** Microsoft Presidio Analyzer/Anonymizer, spaCy (`en_core_web_sm`)
* **Cryptography & Auth:** PyJWT, `cryptography` (AES-GCM / Fernet)
* **Offline ML & Analysis:** ChromaDB (offline synthetic disambiguation index), NetworkX (offline linkage risk graphs), scikit-learn (ablation & PR threshold calibration)
* **Frontend Dashboard:** React 18, TypeScript, Vite, Vanilla CSS
* **Containerization:** Docker, Docker Compose

---

## 4. Repository Structure

```text
PIIShield/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint & health checks
│   │   ├── api/                     # Proxy, Admin, and Analytics route endpoints
│   │   ├── detection/               # Normalizer, structured regex, checksums, Presidio/spaCy
│   │   ├── consolidation/           # Precedence rules & ChromaDB disambiguation client
│   │   ├── policy/                  # Policy engine, models, and versioned rules.yaml
│   │   ├── anonymization/           # Reversible pseudonymizer & encrypted session vault
│   │   ├── gateway/                 # Gateway proxy orchestrator & provider-agnostic LLM client
│   │   ├── response/                # Response scanner, 5-category classifier, de-pseudonymizer
│   │   ├── audit/                   # Redacting logging filters & fail-closed audit logger
│   │   ├── db/                      # PostgreSQL connection, session provider, ORM models
│   │   ├── evaluation/              # Metrics, A/B/C/D ablation, PR curve threshold tuning
│   │   └── offline/                 # NetworkX linkage graph & ChromaDB exemplar builder
│   ├── tests/                       # Unit, integration, regression (12 cases), adversarial
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/                         # React + TypeScript components, pages, services, types
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── config/                          # Configuration and environment profiles
├── data/                            # Synthetic datasets & evaluation corpora
├── docs/                            # Documentation references
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── PIIShield_Spec_v2.md             # Authoritative technical specification
```

---

## 5. Local Setup Instructions

### Prerequisites
* Python 3.11+
* Node.js 20+ & npm
* PostgreSQL 15+ (or Docker)

### Backend Setup

1. **Navigate to the backend directory and create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies and spaCy model:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Start the backend development server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *Health Check:* Visit `http://localhost:8000/health` (returns `{"status": "ok"}`).

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   *Dashboard:* Visit `http://localhost:5173`.

---

## 6. Docker Startup

To spin up the entire environment (PostgreSQL database, FastAPI backend, and React frontend) using Docker Compose:

```bash
docker-compose up --build
```

* **FastAPI Backend:** `http://localhost:8000`
* **Swagger API Docs:** `http://localhost:8000/docs`
* **React Frontend:** `http://localhost:5173`
* **PostgreSQL:** `localhost:5432`
