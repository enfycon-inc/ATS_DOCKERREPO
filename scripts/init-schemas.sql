-- ============================================================
-- ATS Production Database — Schema Initialization
-- Runs ONCE automatically on first PostgreSQL container start
-- ============================================================

-- 1. ATS Application Schema (all NestJS/Prisma app tables)
CREATE SCHEMA IF NOT EXISTS ats;

-- 2. Mass Mail Schema (email campaigns, templates, accounts)
CREATE SCHEMA IF NOT EXISTS mass_mail;

-- 3. Keycloak Schema (managed entirely by Keycloak — DO NOT touch)
CREATE SCHEMA IF NOT EXISTS keycloak;

-- Grant full access to ats_user on all schemas
GRANT ALL PRIVILEGES ON SCHEMA ats       TO ats_user;
GRANT ALL PRIVILEGES ON SCHEMA mass_mail TO ats_user;
GRANT ALL PRIVILEGES ON SCHEMA keycloak  TO ats_user;

-- Allow future tables to be accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA ats       GRANT ALL ON TABLES TO ats_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA mass_mail GRANT ALL ON TABLES TO ats_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak  GRANT ALL ON TABLES TO ats_user;

-- Allow sequences (for SERIAL / auto-increment columns)
ALTER DEFAULT PRIVILEGES IN SCHEMA ats       GRANT ALL ON SEQUENCES TO ats_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA mass_mail GRANT ALL ON SEQUENCES TO ats_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA keycloak  GRANT ALL ON SEQUENCES TO ats_user;
