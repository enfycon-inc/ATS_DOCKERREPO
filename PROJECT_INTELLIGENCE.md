# Master Project Intelligence & Architecture Specification
 
> **System Name:** Multi-Tenant Enterprise Staffing & Recruitment ATS  
> **Target Audience:** AI Coding Assistants / LLMs (Claude, Antigravity, GPT-4, DeepSeek), System Architects, Developers, & DevOps Engineers  
> **Version:** 2.4 (Enterprise Edition)  
> **Last Updated:** August 2026
 
---
 
## 1. System Overview & Core Paradigms
 
This project is a **Multi-Tenant, Multi-Branch, Dual-Market Enterprise Staffing & Applicant Tracking System (ATS)**. It powers both **US IT Staffing** (C2C/W2) and **Domestic Indian Staffing** (Permanent/Contract LPA CTC) operations within a single unified codebase.
 
### Mandatory Architectural Directives for AI Assistants:
1. **Tenant Isolation Boundary (`tenant_id`)**:
   - Every single database query on multi-tenant tables (`candidates`, `jobs`, `recruiter_submissions`, `branches`, `business_units`, `bulk_uploads`) **MUST** filter on `WHERE tenant_id = activeTenantId`. Data from Tenant A must NEVER leak to Tenant B.
2. **Dual Market Partitioning (`market`)**:
   - **`US` (USIT Market)**: USD ($/hr or $/yr), C2C/W2/1099, US Work Authorizations (US Citizen, Green Card, H1B, OPT, CPT).
   - **`INDIA` (Domestic Market)**: INR (Lakhs LPA CTC), Permanent/Contract, Indian Work Authorizations (Indian Citizen, Overseas), Notice Period (15/30/60/90 days), and PAN Card tracking.
3. **Tenant Admin Configurable Candidate CV Pool Policy (`candidate_pool_mode`)**:
   - **`COMBINED_MARKET` (Recommended System Default)**: All Domestic branches in a tenant share all Domestic CVs (`market = 'INDIA'`); all USIT branches share all USIT CVs (`market = 'US'`). Operational job requisitions and submissions remain branch-isolated (`branch_id`).
   - **`STRICT_BRANCH`**: Non-admin recruiters can only search and view candidate CVs created within or assigned to their home office branch (`c.branch_id = user.branchId`).
   - **`ALL_BRANCHES`**: Open workspace sharing across all branches and markets within the tenant.
 
---
 
## 2. Monorepo Repository Structure & Submodule Topology
 
```
c:\Users\enfyc\OneDrive\Desktop\ATS enfy\          (Monorepo Root / Master Docker Repo)
│
├── docker-compose.yml                            (Master 4-Service Container Blueprint)
├── PROJECT_INTELLIGENCE.md                       (This Specification Document)
│
├── ats_frontend_main/                            (Web UI Portal - Next.js 14 / React)
│   ├── GitHub: https://github.com/enfycon-inc/ats_frontend_main.git
│   ├── app/(dashboard)/                          (App Router Pages)
│   │   ├── applicants/                           (Candidates List, Individual & Bulk Import)
│   │   ├── job-posting/                          (Requisition Creation & Matching)
│   │   ├── utility/submissions/                  (Submissions Tracker & L1/L2/L3 Pipelines)
│   │   ├── company/                              (Tenant Settings & Candidate Pool Access Policy)
│   │   └── utility/pods/                         (Recruitment Pod Management)
│   ├── lib/ats-api.ts                            (Central API Client Library)
│   └── constants/navigation.ts                   (Navigation Menu Registry)
│
├── ats_backend/                                  (Core REST API - NestJS / TypeScript)
│   ├── GitHub: https://github.com/enfycon-inc/ats_backend.git
│   └── src/
│       ├── auth/                                 (JWT Auth, Tenant/Branch Resolvers, Profile)
│       ├── candidates/                           (Candidates CRUD, Bulk CV BullMQ Processor)
│       ├── jobs/                                 (Requisitions, Next Code Generator, JD Parser)
│       ├── recruiter-submissions/                (Submissions, L1/L2/L3 Pipeline Transitions)
│       ├── pods/                                 (Recruitment Pods & Round-Robin Routing)
│       ├── branches/                             (Branch Offices Management)
│       ├── database/                             (Database Service & DDL Migrations)
│       └── main.ts                               (Bootstrap & Global NestJS Config)
│
└── resume-parser-main/                           (AI Resume Parser - Python 3.11 / FastAPI)
    ├── GitHub: https://github.com/enfycon-inc/resume-parser.git
    ├── main.py                                   (FastAPI Router: /extract, /parse-jd)
    └── app/                                      (PyMuPDF, python-docx, Gemini NLP Extractor)
```
 
---
 
## 3. Microservice Network Architecture & Data Flow
 
```mermaid
flowchart TD
    subgraph Browser ["Web Browser (Recruiter UI)"]
        UI["Next.js 14 Portal (Port 3000)"]
    end
 
    subgraph Backend ["Core API Layer"]
        Nest["NestJS Backend (Port 5000)"]
        TR["Tenant & Branch Resolver"]
        Guard["JWT Auth Guard"]
    end
 
    subgraph Async ["Async Task & Message Queue"]
        Redis[("Redis Engine (Port 6379)")]
        Bull["BullMQ Queue (bulk_cv)"]
    end
 
    subgraph AI ["AI Parsing Layer"]
        FastAPI["Python FastAPI (Port 8000)"]
        NLP["Gemini NLP / PyMuPDF Extractor"]
    end
 
    subgraph Database ["Persistence Layer"]
        Supabase[("Supabase PostgreSQL (Port 6543)")]
    end
 
    UI -->|REST / JWT| Nest
    Nest --> Guard --> TR
    Nest -->|Persist & Query| Supabase
    Nest -->|Push Tasks| Bull --> Redis
    Redis -->|Process Jobs| Nest
    Nest -->|HTTP /extract| FastAPI --> NLP
```
 
---
 
## 4. Role-Based Access Control (RBAC) & Tenant Security Model
 
| Role | Permissions & Scoping Boundaries |
| :--- | :--- |
| **`SUPER_ADMIN`** | Platform Command Center access across all tenants, global audit logs, tenant approvals, master dictionaries. |
| **`ADMIN` / `TENANT_ADMIN`** | Full workspace authority for their tenant (`tenant_id`). Configures company settings, `candidate_pool_mode`, branch offices, recruitment pods, and user roles. |
| **`ACCOUNT_MANAGER`** | Manages client accounts, approves recruiter submissions (`PENDING_APPROVAL`), assigns jobs to recruiters/pods. |
| **`POD_LEAD` / `DELIVERY_HEAD`** | Manages recruitment pod assignments, reviews pod submissions, monitors recruiter delivery targets. |
| **`RECRUITER`** | Sources candidates, imports resumes, submits candidates to jobs. Candidate search is governed by tenant `candidate_pool_mode`. |
 
---
 
## 5. Complete REST API Endpoint Registry
 
### Auth & Tenant Management (`ats_backend/src/auth`)
- `POST /api/auth/login`: Authenticates user, returns JWT token & user profile.
- `GET /api/auth/me`: Returns profile of active user, tenant details, branch ID, default market, and `candidatePoolMode`.
- `PATCH /api/auth/tenants/my-settings`: Updates tenant workspace configuration (`candidatePoolMode`, pod system toggles).
 
### Candidate Management & Resume Import (`ats_backend/src/candidates`)
- `GET /api/candidates`: Lists candidates for active tenant, filtered by `candidate_pool_mode`, search query, and market.
- `POST /api/candidates/upload-cv`: Single resume upload. Computes SHA-256 binary hash, calls Python parser, updates or creates candidate profile.
- `POST /api/candidates/bulk-upload`: Asynchronous mass resume upload (up to 500 files per batch). Pushes jobs to BullMQ Redis queue and returns `bulkUploadId` in < 200 ms.
- `GET /api/candidates/bulk-uploads`: Retrieves historical bulk upload batch runs.
- `GET /api/candidates/bulk-uploads/:id`: Polls live progress of active bulk parsing batch run.
 
### Job Requisitions (`ats_backend/src/jobs`)
- `GET /api/jobs`: Lists job requisitions for active tenant/branch.
- `POST /api/jobs`: Creates a new job requisition with assigned client, bill/pay rates, skills, and optional `podId`.
- `GET /api/jobs/next-code`: Returns auto-generated sequential job code (e.g. `ENFY-JOB-2608-00042`).
- `POST /api/jobs/parse-jd`: Calls Python NLP service to parse raw job description text into structured title, skills, experience, and rates.
 
### Submissions & Pipeline Tracker (`ats_backend/src/recruiter-submissions`)
- `GET /api/submissions`: Lists candidate submissions, supporting search filters, date ranges, and status filters.
- `POST /api/submissions`: Submits a candidate to a job requisition with status `PENDING_APPROVAL`.
- `PATCH /api/submissions/:id`: Updates submission final status (`SUBMITTED`, `REJECTED`, `OFFER`, `JOIN`) or interview stages (`l1_status`, `l2_status`, `l3_status`).
 
### Recruitment Pods (`ats_backend/src/pods`)
- `GET /api/pods`: Lists active recruitment delivery pods.
- `POST /api/pods`: Creates a new recruitment pod with lead and members.
 
---
 
## 6. Environment Variables Catalog
 
### Backend (`ats_backend/.env`):
```env
PORT=5000
DATABASE_URL=postgresql://postgres.zqpxnnsbbqdlhememsyj:EWhbqnM6IWe5IJaV@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres
JWT_SECRET=super-secret-jwt-key-ats-backend
REDIS_HOST=localhost
REDIS_PORT=6379
PARSER_SERVICE_URL=http://localhost:8000
```
 
### Frontend (`ats_frontend_main/.env`):
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXTAUTH_SECRET=nextauth-secret-key-frontend
```
 
### Python Parser (`resume-parser-main/.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
 
---
 
## 7. Database Tables Schema Definition
 
```sql
-- TENANTS TABLE
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  domain VARCHAR(100) UNIQUE NOT NULL,
  default_market VARCHAR(10) DEFAULT 'US',
  candidate_pool_mode VARCHAR(50) DEFAULT 'COMBINED_MARKET',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
 
-- CANDIDATES TABLE
CREATE TABLE IF NOT EXISTS candidates (
  id SERIAL PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  branch_id UUID,
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(50),
  raw_current_location VARCHAR(255),
  total_experience_years NUMERIC,
  current_ctc NUMERIC,
  notice_period_days INTEGER,
  market VARCHAR(10) DEFAULT 'US',
  source VARCHAR(100),
  file_hash VARCHAR(64),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
 
-- RESUMES TABLE
CREATE TABLE IF NOT EXISTS resumes (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  file_size INTEGER,
  file_mime VARCHAR(100),
  raw_text TEXT,
  parsed_json JSONB,
  file_hash VARCHAR(64),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
 
-- BULK UPLOADS TRACKING TABLES
CREATE TABLE IF NOT EXISTS bulk_uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  created_by VARCHAR(255),
  total_files INTEGER DEFAULT 0,
  processed_files INTEGER DEFAULT 0,
  failed_files INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'processing',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
 
CREATE TABLE IF NOT EXISTS bulk_upload_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bulk_upload_id UUID REFERENCES bulk_uploads(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'queued',
  candidate_id INTEGER,
  candidate_name VARCHAR(255),
  candidate_email VARCHAR(255),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
 
---
 
## 8. Summary for Future AI Agents
 
When interacting with or extending this codebase:
- **Always preserve tenant scoping (`tenant_id = activeTenantId`)** across all database queries and DTOs.
- **Never hardcode arbitrary pixel heights or static offsets** in frontend UI layouts. Use dynamic flex/grid wrappers and HSL color variables.
- **Run build checks (`npx tsc --noEmit`)** on modified projects before declaring completion.
