# 🚀 AWS VPS Production Deployment & GitHub Actions CI/CD Guide

This guide walks you through publishing and deploying the **Enfycon ATS Multi-Tenant Platform** on an **AWS VPS (EC2 or Amazon Lightsail)** with **GitHub Actions CI/CD** and **Automatic Let's Encrypt SSL Certificates**.

---

## 📋 Prerequisites & Sizing

### Recommended AWS VPS Specifications
| Cloud Provider | Instance Type | Specs | Est. Cost |
| :--- | :--- | :--- | :--- |
| **AWS Lightsail** (Recommended for simplicity) | 4 GB RAM Plan | 2 vCPUs, 4 GB RAM, 80 GB SSD | ~$20 / month |
| **AWS EC2** | `t3.medium` or `t3.large` | 2 vCPUs, 4–8 GB RAM | ~$30–$60 / month |

- **Operating System:** Ubuntu 22.04 LTS or 24.04 LTS (x86_64).

---

## ⚙️ Step 1: AWS Security Group (Firewall) Configuration

In your **AWS EC2 / Lightsail Console**, ensure the following **Inbound Firewall Rules** are open:

| Port | Protocol | Source | Purpose |
| :--- | :--- | :--- | :--- |
| `22` | TCP | `0.0.0.0/0` *(or your IP)* | SSH Access & GitHub Actions CI/CD |
| `80` | TCP | `0.0.0.0/0` | HTTP (Caddy Automatic SSL Redirection) |
| `443` | TCP | `0.0.0.0/0` | HTTPS (Secure Web Traffic) |
| `443` | UDP | `0.0.0.0/0` | HTTP/3 QUIC (High Performance Traffic) |

---

## 🌐 Step 2: DNS Records Setup (Route 53 / Cloudflare / GoDaddy)

Point your domain to your **AWS VPS Public IP address**:

| Type | Host / Name | Value / Target | Notes |
| :--- | :--- | :--- | :--- |
| **A** | `*.enfyjobs.com` | `<AWS_VPS_PUBLIC_IP>` | Wildcard for all tenant subdomains (e.g. `deb.enfyjobs.com`) |
| **A** | `enfyjobs.com` | `<AWS_VPS_PUBLIC_IP>` | Root domain |
| **A** | `api.enfyjobs.com` | `<AWS_VPS_PUBLIC_IP>` | Dedicated Backend API endpoint |
| **A** | `auth.enfyjobs.com` | `<AWS_VPS_PUBLIC_IP>` | Keycloak Identity & SSO Provider |
| **A** | `db.enfyjobs.com` | `<AWS_VPS_PUBLIC_IP>` | pgAdmin 4 Database Web Console & PostgreSQL |

*(Note: Caddy automatically requests and renews valid SSL certificates for all subdomains and custom domains on the fly!)*

---

## 💻 Step 3: One-Time VPS Setup

SSH into your new AWS VPS:
```bash
ssh -i your-key.pem ubuntu@<AWS_VPS_PUBLIC_IP>
```

Run the **One-Click Initializer Script**:
```bash
curl -sSL https://raw.githubusercontent.com/enfycon-inc/ATS_DOCKERREPO/main/scripts/setup_vps.sh | bash
```

This automatically:
- Installs **Docker Engine** & **Docker Compose plugin**.
- Allocates a **4GB Swap file** (prevents out-of-memory errors during Next.js/PyTorch compilation).
- Configures **UFW Firewall**.
- Sets up `/var/www/ats` deployment directory.

---

## 🔐 Step 4: Add GitHub Actions Secrets

In your GitHub repository:
👉 Go to **Settings** > **Secrets and variables** > **Actions** > **New repository secret**

Add the following secrets:

### 1. SSH Server Connection Secrets
- **`VPS_HOST`**: Your AWS VPS Public IP (e.g. `3.112.45.189`).
- **`VPS_USERNAME`**: SSH username (`ubuntu` for Ubuntu EC2/Lightsail).
- **`VPS_SSH_KEY`**: Your private SSH key (contents of `your-key.pem`).
- **`VPS_PORT`**: `22` (default).

### 2. Production Environment Variables (Optional but Recommended)
- **`PROD_ENV_BACKEND`**: Production `.env` for `ats_backend` (Supabase DB URL, Keycloak issuer, JWT secrets).
- **`PROD_ENV_FRONTEND`**: Production `.env` for `ats_frontend_main` (`AUTH_SECRET`, Google/Microsoft OAuth credentials).
- **`PROD_ENV_PARSER`**: Production `.env` for `resume-parser-main` (Gemini API keys, Celery redis URLs).

---

## 🚀 Step 5: Deploy via GitHub Actions

1. Commit and push your code to the `main` branch:
   ```bash
   git add .
   git commit -m "feat: setup AWS VPS production deployment and CI/CD"
   git push origin main
   ```
2. In GitHub, open the **Actions** tab:
   - You will see the **"CI/CD Production Deployment to AWS VPS"** workflow executing.
   - It will verify the builds, connect to your AWS VPS via SSH, pull the latest code, build the production Docker containers, and start Caddy with SSL!

---

## 🩺 Step 6: Verifying the Live Deployment

After deployment completes:
- **Tenant Subdomain:** Visit `https://deb.enfyjobs.com` (Secured with Let's Encrypt HTTPS).
- **Swagger API Docs:** Visit `https://api.enfyjobs.com/docs` or `https://enfyjobs.com/docs`.
- **Zero-Trust Login:** Test Google / Microsoft 1-click SSO on the live HTTPS domain.
- **Custom Domains:** Test mapping any custom domain (e.g. `careers.myclient.com`) in the `/company` settings page.
