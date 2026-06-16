# Multi-Tenant Integration Guide: Frontend to Backend

This document details the multi-tenant architecture and user approval systems implemented in the frontend, describing exactly how they connect to the NestJS backend. Use this report to replicate these structures in a new codebase or branch.

---

## 1. Domain/Subdomain Routing & Middleware
The frontend isolates tenants using subdomains (e.g., `company-slug.enfycon.com`). The middleware intercepts every request, extracts the subdomain, and forwards it to Next.js server components and the backend.

### Implementation Details:
* **File Location**: `ats_frontend/middleware.ts`
* **Flow**:
  1. Extracts the `Host` header from the request.
  2. Parses the subdomain, ignoring `localhost` hosts, `www`, and standard root access points like `app`.
  3. Attaches the parsed subdomain to request and response headers as `x-tenant-domain`. This allows server components and pages to identify the tenant context.

```typescript
// Example from middleware.ts
const hostname = request.headers.get('host') || '';
let subdomain = '';
// Extraction logic...
if (subdomain && subdomain !== 'www' && subdomain !== 'app') {
  response.headers.set('x-tenant-domain', subdomain);
  request.headers.set('x-tenant-domain', subdomain);
}
```

---

## 2. Authentication & Session Sync (NextAuth + Local Sync)
The login flow establishes the session on both the Next.js server side (via NextAuth) and client side (via LocalStorage JWT sync).

### Implementation Details:
* **Server-Side Session**:
  * **File Location**: `ats_frontend/lib/auth.ts`
  * **Flow**:
    1. A user logs in via credentials.
    2. NextAuth's `authorize` hook hits the backend API `/api/auth/login`. 
    3. If the backend is running inside Docker, it queries `http://backend:5000`. If running locally, it falls back to `http://127.0.0.1:5000`.
    4. Upon successful login, the backend returns the user profile, their scoped `tenantId`, `roles`, and `permissions` array.
    5. These values are encoded into the NextAuth JWT token and session callback.
* **Client-Side Session Sync**:
  * **File Location**: `ats_frontend/components/partials/auth/login-form.tsx`
  * **Flow**:
    1. If NextAuth successfully signs in the user, the frontend immediately executes `atsApi.auth.login(email, password)`.
    2. This fetches the raw backend HS256 JWT access token and saves it in `localStorage` (`ats_access_token` and `ats_current_user`).
    3. The frontend API client automatically attaches this token as `Authorization: Bearer <token>` to all subsequent data fetches.

---

## 3. Frontend API Client Definitions
The backend endpoints mapping for multi-tenancy registration and administrative approvals are declared inside the typed API client.

### Implementation Details:
* **File Location**: `ats_frontend/lib/ats-api.ts`
* **Core Endpoints**:

| Method | Endpoint | API Wrapper function | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register-tenant` | `registerTenant(data)` | Public self-signup for new company tenants. |
| `GET` | `/api/auth/approvals/pending` | `listPendingApprovals()` | Lists registered users/companies awaiting approval. |
| `POST` | `/api/auth/approvals/approve/:id` | `approveUser(userId, market, subdomain)` | Approves registration, configures subdomain and market. |
| `GET` | `/api/auth/tenants` | `listTenants()` | Lists all active corporate tenants on the platform. |
| `PATCH` | `/api/auth/tenants/:id/market` | `updateTenantMarket(tenantId, market)` | Toggles recruitment market settings (US vs. India). |

---

## 4. Tenant Registration (Self-Signup UI)
A public-facing workspace creation page allows new clients to register.

### Implementation Details:
* **File Location**: `ats_frontend/components/partials/auth/reg-form.tsx`
* **Flow**:
  1. The user inputs company name, desired subdomain, admin email, and password.
  2. Submits payload to `atsApi.auth.registerTenant(...)`.
  3. Displays a confirmation message stating that the registration is pending platform administrator approval.

---

## 5. Platform Tenant & Approvals Panel
A dashboard route accessible only to platform `SUPER_ADMIN` accounts.

### Implementation Details:
* **File Location**: `ats_frontend/app/[locale]/(protected)/utility/approvals/page.tsx`
* **Features**:
  * **Guard**: Verifies `user?.roles?.includes("SUPER_ADMIN")` inside a `useEffect` hook. Non-admins receive an "Access Denied" screen.
  * **Tab 1: Pending Approvals**: Lists all users waiting for approval. Displays company name, date registered, and requested role.
    * Allows the super admin to specify their workspace subdomain.
    * Allows the super admin to select the operating recruitment market layout (`US IT Staffing` or `Indian Staffing`).
    * Click "Approve" to send the activation hook to the backend.
  * **Tab 2: Active Tenants**: Displays all active company workspaces, their domains, and a live toggle to change their staffing market layout configuration dynamically.
