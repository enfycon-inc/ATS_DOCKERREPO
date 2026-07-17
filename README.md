# ATS Multi-Service Docker Development Setup 🚀

> [!IMPORTANT]
> **For AI Agents & LLMs:** Before analyzing code or making modifications, please read the [PROJECT_ARCHITECTURE_BLUEPRINT.md](PROJECT_ARCHITECTURE_BLUEPRINT.md) file at the root. It contains the system topology, multi-tenant rules, submission workflow logic, and file architecture map.
> 
> *Constraint:* If you make any architectural, database, or API changes during this session, **you must update the blueprint file** to keep it accurate, and clearly inform the user of the update in your summary.

Welcome to the central Docker orchestrator for the Applicant Tracking System (ATS). This repository contains the unified development environment configuration using Docker Compose to run all frontend, backend, parser, and database services simultaneously.

---

## 🛠️ Quick Start Guide

To run this entire stack on your local machine, follow these simple steps:

### 1. Prerequisites
Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on your system.

### 2. Setup Directory structure
Create a parent directory called `ATS enfy` (if you haven't already), then clone this docker repository and the three active codebases inside it:

```bash
# Step 1: Clone this docker repository and enter the directory
git clone https://github.com/enfycon-inc/ATS_DOCKERREPO.git "ATS enfy"
cd "ATS enfy"

# Step 2: Clone the three individual service repositories
git clone https://github.com/enfycon-inc/ats_frontend.git ats_frontend
git clone https://github.com/enfycon-inc/ats_backend.git ats_backend
git clone https://github.com/enfycon-inc/resume-parser-main.git resume-parser-main
```

Your folder structure should look like this:
```text
ATS enfy/
├── .gitignore
├── README.md
├── docker-compose.yml
├── ats_frontend/         # Next.js Frontend
├── ats_backend/          # NestJS Backend
└── resume-parser-main/   # FastAPI Parser & Celery Worker
```

### 3. Start the Environment
Run the following command from the root `ATS enfy` folder to build and start all services in the background:
```bash
docker compose up -d
```

---

## 🌐 Endpoints & Services

Once the containers are running, you can access the services at these URLs:

| Service Name | Port | Description | URL |
| :--- | :--- | :--- | :--- |
| **Frontend Portal** | `3000` | Next.js Recruiter UI | [http://localhost:3000](http://localhost:3000) |
| **ATS Backend Core** | `5000` | Node.js / NestJS API | [http://localhost:5000](http://localhost:5000) |
| **FastAPI Service** | `8000` | Python Parser Microservice | [http://localhost:8000](http://localhost:8000) |
| **Celery Worker** | *Internal* | Background Processing | *Managed by Docker* |
| **Redis Queue** | `6379` | Message Broker | *localhost:6379* |

---

## 💻 Development & Logs

### Instant Hot-Reloading
This setup maps your local folders directly inside the running containers. When you edit and save any file in VS Code (`ats_frontend`, `ats_backend`, or `resume-parser-main`), the active container will automatically detect the changes and **instantly reload** without requiring a rebuild!

### Useful Commands

* **Stop all containers:**
  ```bash
  docker compose down
  ```
* **View/Stream logs for a service (e.g., backend):**
  ```bash
  docker compose logs -f backend
  ```
* **View/Stream logs for the frontend:**
  ```bash
  docker compose logs -f frontend
  ```
