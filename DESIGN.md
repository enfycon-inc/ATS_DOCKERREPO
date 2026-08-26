# Enfycon ATS — Design System Specification

## Overview
Enfycon ATS is an AI-powered Enterprise Recruitment & Staffing Platform designed for US IT & Indian talent acquisition workflows. This document specifies the design tokens, visual identity, components, and layout guidelines for authentication and dashboard experiences.

---

## 1. Brand Identity & Visual Language

### Brand Concept
- **Identity**: Intelligent, Executive, Sleek, Precision-driven.
- **Core Aesthetic**: Dark mesh hero gradients, high-contrast crisp forms, subtle glassmorphism (`backdrop-blur-md`), vibrant indigo & cyan accents.
- **Logo Symbol**: Interconnected nodes forming an 'E' emblem with AI spark highlights.

### Color Tokens

```css
/* Color Palette */
:root {
  /* Brand Primaries */
  --brand-primary: #4F46E5;       /* Indigo 600 */
  --brand-primary-hover: #4338CA; /* Indigo 700 */
  --brand-accent: #06B6D4;        /* Cyan 500 */
  --brand-accent-glow: rgba(6, 182, 212, 0.25);

  /* Gradients */
  --gradient-hero: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #090D16 100%);
  --gradient-cta: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #3B82F6 100%);
  --gradient-card: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);

  /* Backgrounds */
  --bg-surface: #FFFFFF;
  --bg-surface-dark: #0F172A;
  --bg-muted: #F8FAFC;
  --bg-muted-dark: #1E293B;

  /* Typography Colors */
  --text-main: #0F172A;
  --text-muted: #64748B;
  --text-inverse: #F8FAFC;
}
```

---

## 2. Typography & Hierarchy

- **Primary Font**: Inter / System UI Font Stack (`font-sans`).
- **Heading Scales**:
  - `Display / Hero Title`: `36px` to `42px`, `font-bold` / `font-extrabold`, leading `1.2`.
  - `H1 / Section Title`: `24px` to `28px`, `font-semibold`, leading `1.3`.
  - `Body Standard`: `14px` to `16px`, `font-normal`, leading `1.5`.
  - `Captions & Badges`: `12px`, `font-medium`, `tracking-wide`.

---

## 3. Login & Authentication UX Guidelines

### Layout & Composition
- **Desktop (≥ 1024px)**: 50/50 Split layout.
  - Left Canvas: Deep gradient mesh with floating ambient glow orbs, feature value props, and an interactive "Talent Match Engine" CSS/SVG card preview.
  - Right Canvas: Centered auth card container with top logo, clean input fields, micro-interactions, and quick registration access.
- **Mobile (< 1024px)**: Single column with top centered logo, title, and compact glassmorphism form card.

### Input & Micro-Interactions
- Icons inside inputs (`Mail`, `Lock`) aligned left with `text-slate-400`.
- Focus Ring: `ring-2 ring-indigo-500/20 border-indigo-500` with `transition-all duration-200`.
- Interactive Password Toggle: Smooth icon toggle with clear aria label.
- CTA Button: Gradient background with subtle hover lift (`translate-y-[-1px]`), scale feedback, and spinner loading state.

---

## 4. Multi-Tenant Email & Custom Domain Architecture

### Overview
EnfySync ATS provides a flexible 3-tier email delivery and custom domain architecture allowing tenant administrators to customize how transactional (welcome emails, password resets) and outbound communications (candidate offers, interview invites) are dispatched:

### Delivery Models

#### Model 1: Direct Mail Connection (BYOE - "Bring Your Own Email")
- **Target**: Staffing agencies & corporate recruiting teams with existing mail infrastructure.
- **Providers**: Microsoft 365 (Graph API), Google Workspace (OAuth2), or Custom SMTP (Host/Port/TLS).
- **Execution Flow**:
  - Tenant Admin connects their mail account in **Settings $\rightarrow$ Email & Domains**.
  - ATS stores encrypted OAuth tokens/credentials in `mass_mail.email_accounts` flagged as `is_default = true`.
  - All transactional and candidate emails dispatch directly via the tenant's mailbox (`hr@enfycon.com`, `careers@client.com`).
- **Benefits**: Zero platform email costs, 100% inbox deliverability, zero DNS setup required.

#### Model 2: White-Label Custom Domain Delegation (Enterprise Tier)
- **Target**: Enterprise clients desiring automated sending from `no-reply@<their-domain>.com`.
- **Execution Flow**:
  - Tenant enters their custom root domain (e.g. `acme.com`).
  - Backend generates 3 DKIM CNAME records + SPF TXT validation strings from the platform relay (AWS SES / Resend).
  - Tenant copies DNS records into their DNS registrar (Cloudflare, GoDaddy, Route53).
  - Once verified, the platform relay cryptographically signs and dispatches emails as `no-reply@acme.com`.

#### Model 3: Default Platform Subdomain (Zero-Config Default)
- **Target**: New tenants, trial users, or standard platform accounts.
- **Execution Flow**:
  - Automatically enabled out-of-the-box.
  - Sends via the platform relay with dynamic `From` header: `"${tenant.name}" <no-reply@${tenant.subdomain}.enfyjobs.com>`.

### Centralized Dispatch Hierarchy
All system email triggers (New User Credentials, Password Setup, Interview Invites) route through `TenantMailerService`:
```
Tenant Email Request
   │
   ├─► Check Model 1: Is a default tenant email account (Microsoft/Google/SMTP) connected?
   │     └─► YES: Dispatch via Microsoft Graph / Google API / Tenant SMTP
   │
   ├─► Check Model 2: Is a verified custom domain configured?
   │     └─► YES: Dispatch via Platform Relay with `From: no-reply@<custom_domain>`
   │
   └─► FALLBACK (Model 3): Dispatch via Platform Relay with `From: no-reply@<subdomain>.enfyjobs.com`
```

