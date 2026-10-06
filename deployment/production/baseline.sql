-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "ats";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "mass_mail";

-- CreateTable
CREATE TABLE "ats"."tenants" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(255) NOT NULL,
    "logo_url" TEXT,
    "site_title" VARCHAR(255),
    "domain" VARCHAR(255),
    "status" VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    "default_market" VARCHAR(50) NOT NULL DEFAULT 'US',
    "user_limit" INTEGER NOT NULL DEFAULT 5,
    "prefix_code" VARCHAR(10),
    "pod_system_enabled" BOOLEAN NOT NULL DEFAULT true,
    "max_branches" INTEGER NOT NULL DEFAULT 5,
    "candidate_pool_mode" VARCHAR(50) NOT NULL DEFAULT 'COMBINED_MARKET',
    "email_dispatch_mode" VARCHAR(50) NOT NULL DEFAULT 'DEFAULT_SUBDOMAIN',
    "custom_email_domain" VARCHAR(255),
    "custom_email_domain_verified" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "job_assignment_options" JSONB DEFAULT '{}',
    "job_assignment_mode" VARCHAR(50) DEFAULT 'AUTO',
    "job_code_pattern" VARCHAR(200) DEFAULT '{BRANCH}-{UNIT}-{YYMMDD}-{SEQ}',
    "enforce_job_code_pattern" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "tenants_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."job_recruiters" (
    "job_id" UUID NOT NULL,
    "recruiter_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "job_recruiters_pkey" PRIMARY KEY ("job_id","recruiter_id")
);

-- CreateTable
CREATE TABLE "ats"."tenant_counters" (
    "tenant_id" UUID NOT NULL,
    "entity_type" VARCHAR(50) NOT NULL,
    "current_value" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "tenant_counters_pkey" PRIMARY KEY ("tenant_id","entity_type")
);

-- CreateTable
CREATE TABLE "ats"."tenant_domains" (
    "id" SERIAL NOT NULL,
    "tenant_id" UUID NOT NULL,
    "domain_name" VARCHAR(255) NOT NULL,
    "is_primary" BOOLEAN NOT NULL DEFAULT false,
    "verification_token" VARCHAR(255),
    "verification_status" VARCHAR(50) NOT NULL DEFAULT 'VERIFIED',
    "ssl_status" VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    "verified_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tenant_domains_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."tenant_auth_settings" (
    "tenant_id" UUID NOT NULL,
    "allow_password_login" BOOLEAN NOT NULL DEFAULT true,
    "allow_microsoft_sso" BOOLEAN NOT NULL DEFAULT false,
    "allow_google_sso" BOOLEAN NOT NULL DEFAULT false,
    "enforce_sso_only" BOOLEAN NOT NULL DEFAULT false,
    "require_mfa" BOOLEAN NOT NULL DEFAULT false,
    "allow_personal_emails" BOOLEAN NOT NULL DEFAULT true,
    "allowed_email_domains" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "microsoft_tenant_id" VARCHAR(255),
    "microsoft_client_id" VARCHAR(255),
    "microsoft_client_secret" VARCHAR(255),
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tenant_auth_settings_pkey" PRIMARY KEY ("tenant_id")
);

-- CreateTable
CREATE TABLE "ats"."tenant_email_domains" (
    "id" SERIAL NOT NULL,
    "tenant_id" UUID NOT NULL,
    "email_domain" VARCHAR(255) NOT NULL,
    "sender_address" VARCHAR(255) NOT NULL,
    "dkim_tokens" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "dkim_verified" BOOLEAN NOT NULL DEFAULT false,
    "spf_verified" BOOLEAN NOT NULL DEFAULT false,
    "status" VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "verified_at" TIMESTAMPTZ(6),

    CONSTRAINT "tenant_email_domains_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."tenant_dice_integrations" (
    "tenant_id" UUID NOT NULL,
    "client_id" VARCHAR(255),
    "client_secret" TEXT,
    "account_id" VARCHAR(255),
    "access_token" TEXT,
    "token_expires_at" TIMESTAMPTZ(6),
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "daily_view_limit" INTEGER NOT NULL DEFAULT 500,
    "views_used_today" INTEGER NOT NULL DEFAULT 0,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tenant_dice_integrations_pkey" PRIMARY KEY ("tenant_id")
);

-- CreateTable
CREATE TABLE "ats"."branches" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "code" VARCHAR(50),
    "city" VARCHAR(100),
    "state" VARCHAR(100),
    "country" VARCHAR(100) NOT NULL DEFAULT 'India',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "market" VARCHAR(50) NOT NULL DEFAULT 'INDIA',
    "allow_none" BOOLEAN NOT NULL DEFAULT false,
    "allow_pods" BOOLEAN NOT NULL DEFAULT true,
    "allow_all" BOOLEAN NOT NULL DEFAULT true,
    "allow_unassigned" BOOLEAN NOT NULL DEFAULT true,
    "pod_distribution_strategy" VARCHAR(50) NOT NULL DEFAULT 'AUTO',
    "require_am_job_approval" BOOLEAN NOT NULL DEFAULT true,
    "require_job_approval" BOOLEAN NOT NULL DEFAULT true,
    "roles_requiring_approval" TEXT,
    "default_job_approver_role" VARCHAR(50) DEFAULT 'POD_LEAD',
    "allowed_job_approver_roles" TEXT,
    "approval_routing_mode" VARCHAR(50) DEFAULT 'FLEXIBLE',
    "timezone" VARCHAR(100) DEFAULT 'Asia/Kolkata',
    "work_start_time" VARCHAR(20) DEFAULT '09:00',
    "work_end_time" VARCHAR(20) DEFAULT '18:00',
    "working_days" TEXT,
    "shift_timing" VARCHAR(100) DEFAULT 'General Shift',
    "break_duration_minutes" INTEGER DEFAULT 60,
    "enable_global_remarks" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "selected_global_remark_ids" TEXT DEFAULT 'ALL',

    CONSTRAINT "branches_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."business_units" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "code" VARCHAR(50),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "branch_id" UUID,
    "shift_timing" VARCHAR(100) DEFAULT 'General Shift',
    "timezone" VARCHAR(100) DEFAULT 'Asia/Kolkata',
    "work_end_time" VARCHAR(20) DEFAULT '18:00',
    "work_start_time" VARCHAR(20) DEFAULT '09:00',
    "break_duration_minutes" INTEGER DEFAULT 60,
    "working_days" TEXT[] DEFAULT ARRAY['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']::TEXT[],
    "allow_all" BOOLEAN NOT NULL DEFAULT true,
    "allow_none" BOOLEAN NOT NULL DEFAULT false,
    "allow_pods" BOOLEAN NOT NULL DEFAULT true,
    "allow_unassigned" BOOLEAN NOT NULL DEFAULT true,
    "pod_distribution_strategy" VARCHAR(50) NOT NULL DEFAULT 'AUTO',
    "job_code_pattern" VARCHAR(200),
    "market_segment_id" UUID,
    "address" VARCHAR(500),
    "city" VARCHAR(100),
    "state" VARCHAR(100),
    "zip_code" VARCHAR(20),

    CONSTRAINT "business_units_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."market_segments" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID,
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(20) NOT NULL,
    "description" VARCHAR(500),
    "default_currency" VARCHAR(10) NOT NULL DEFAULT 'USD',
    "default_timezone" VARCHAR(100) NOT NULL DEFAULT 'America/New_York',
    "default_shift" VARCHAR(100) NOT NULL DEFAULT 'General Shift',
    "default_start_time" VARCHAR(20) DEFAULT '09:00',
    "default_end_time" VARCHAR(20) DEFAULT '18:00',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "market_segments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."system_roles" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(100) NOT NULL,
    "system_key" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "permissions" JSONB NOT NULL DEFAULT '[]',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "system_roles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."custom_roles" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "branch_id" UUID,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "is_system" BOOLEAN NOT NULL DEFAULT false,
    "base_role_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" UUID,
    "system_role_id" UUID,
    "permissions" JSONB NOT NULL DEFAULT '[]',
    "business_unit_id" UUID,

    CONSTRAINT "custom_roles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."pods" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "branch_id" UUID,
    "name" VARCHAR(255) NOT NULL,
    "pod_head_id" UUID,
    "description" TEXT,
    "is_available_for_assignment" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "business_unit_id" UUID,

    CONSTRAINT "pods_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."users" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "keycloak_id" VARCHAR(255),
    "email" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(128),
    "last_name" VARCHAR(128),
    "full_name" VARCHAR(255) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "is_approved" BOOLEAN NOT NULL DEFAULT true,
    "profile_picture" TEXT,
    "role_id" UUID,
    "assigned_role_ids" UUID[] DEFAULT ARRAY[]::UUID[],
    "branch_id" UUID,
    "assigned_branch_ids" UUID[] DEFAULT ARRAY[]::UUID[],
    "branch_roles" JSONB NOT NULL DEFAULT '{}',
    "business_unit_id" UUID,
    "job_reviewer_id" UUID,
    "pod_id" UUID,
    "last_login_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "requested_role" VARCHAR(128),

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."user_invitations" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "full_name" VARCHAR(255),
    "role_id" UUID,
    "branch_id" UUID,
    "pod_id" UUID,
    "invitation_token" VARCHAR(255) NOT NULL,
    "token_expires_at" TIMESTAMPTZ(6) NOT NULL,
    "created_by" UUID,
    "is_accepted" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "system_role_id" UUID,

    CONSTRAINT "user_invitations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."clients" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "client_code" VARCHAR(100),
    "client_name" VARCHAR(255) NOT NULL,
    "contact_number" VARCHAR(100),
    "website" VARCHAR(255),
    "industry" VARCHAR(100),
    "state" VARCHAR(100),
    "city" VARCHAR(100),
    "status" VARCHAR(50) NOT NULL DEFAULT 'Active',
    "category" VARCHAR(100),
    "primary_owner" VARCHAR(255),
    "business_unit" VARCHAR(100),
    "ownership" VARCHAR(100),
    "display_on_job_posting" BOOLEAN NOT NULL DEFAULT true,
    "created_by" UUID,
    "modified_by" VARCHAR(255),
    "federal_id" VARCHAR(100),
    "email_id" VARCHAR(255),
    "fax" VARCHAR(100),
    "payment_terms" VARCHAR(100),
    "address" TEXT,
    "client_lead" VARCHAR(255),
    "postal_code" VARCHAR(50),
    "country" VARCHAR(100),
    "practice" VARCHAR(100),
    "required_documents" TEXT,
    "tag" VARCHAR(100),
    "client_short_name" VARCHAR(100),
    "geopolitical_zone" VARCHAR(100),
    "primary_business_unit" VARCHAR(100),
    "facility_management" VARCHAR(100),
    "branch_id" UUID,
    "market" VARCHAR(50) NOT NULL DEFAULT 'US',
    "end_client_name" VARCHAR(255),
    "is_same_as_primary" BOOLEAN NOT NULL DEFAULT true,
    "contact_person" VARCHAR(255),
    "contact_designation" VARCHAR(255),
    "gstin" VARCHAR(100),
    "pan_number" VARCHAR(100),
    "currency" VARCHAR(20) NOT NULL DEFAULT 'USD',
    "tier_rating" VARCHAR(50),
    "credit_check_status" VARCHAR(50),
    "fillability_score" VARCHAR(50),
    "vetting_notes" TEXT,
    "onboarding_status" VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    "msa_signed" BOOLEAN NOT NULL DEFAULT false,
    "sow_executed" BOOLEAN NOT NULL DEFAULT false,
    "coi_received" BOOLEAN NOT NULL DEFAULT false,
    "vendor_portal_created" BOOLEAN NOT NULL DEFAULT false,
    "stop_notifications" BOOLEAN NOT NULL DEFAULT false,
    "about_company" TEXT,
    "approval_status" VARCHAR(50) DEFAULT 'APPROVED',
    "assigned_approver_id" UUID,
    "approved_by" UUID,
    "approved_at" TIMESTAMPTZ(6),
    "rejection_reason" TEXT,
    "deleted_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "commission_percentage" DECIMAL(5,2),
    "contract_markup" DECIMAL(5,2),

    CONSTRAINT "clients_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."resumes" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "filename" VARCHAR(255),
    "candidate_name" VARCHAR(255),
    "email" VARCHAR(255),
    "file_hash" VARCHAR(255),
    "parsed_json" JSONB,
    "raw_text" TEXT,
    "embedding" TEXT,
    "file_data" BYTEA,
    "file_mime" VARCHAR(150),
    "file_size" INTEGER,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "resumes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."candidates" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID,
    "branch_id" UUID,
    "candidate_code" VARCHAR(100),
    "first_name" VARCHAR(255),
    "last_name" VARCHAR(255),
    "full_name" VARCHAR(255),
    "email" VARCHAR(255),
    "phone" VARCHAR(50),
    "market" VARCHAR(50) NOT NULL DEFAULT 'US',
    "source" VARCHAR(100),
    "work_authorization" VARCHAR(100),
    "raw_current_location" TEXT,
    "raw_current_designation" TEXT,
    "total_experience_years" DECIMAL(4,1),
    "relevant_experience_years" DECIMAL(4,1),
    "current_ctc" DECIMAL(10,2),
    "expected_ctc" DECIMAL(10,2),
    "current_company" VARCHAR(255),
    "availability_to_start" VARCHAR(100),
    "notice_period_days" INTEGER NOT NULL DEFAULT 0,
    "serving_notice" BOOLEAN NOT NULL DEFAULT false,
    "last_working_day" DATE,
    "pan_card" VARCHAR(10),
    "preferred_locations" TEXT[],
    "skills" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "resume_record_id" UUID,
    "uploaded_by_user_id" UUID,
    "uploaded_by_name" VARCHAR(255),
    "deleted_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "candidates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."jobs" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "branch_id" UUID,
    "business_unit_id" UUID,
    "job_code" VARCHAR(100) NOT NULL,
    "job_title" VARCHAR(255) NOT NULL,
    "job_type" VARCHAR(100) NOT NULL DEFAULT 'Full-time',
    "job_description" TEXT,
    "skills_required" TEXT[],
    "secondary_skills" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "state" VARCHAR(100),
    "city" VARCHAR(100),
    "country" VARCHAR(100),
    "client_job_id" VARCHAR(100),
    "visa_type" VARCHAR(500),
    "pay_rate_min" DECIMAL(10,2),
    "pay_rate_max" DECIMAL(10,2),
    "pay_currency" VARCHAR(10) DEFAULT 'INR',
    "pay_term" VARCHAR(50) DEFAULT 'LPA',
    "client_bill_rate_min" DECIMAL(10,2),
    "client_bill_rate_max" DECIMAL(10,2),
    "client_bill_currency" VARCHAR(10) DEFAULT 'INR',
    "client_bill_term" VARCHAR(50) DEFAULT 'LPA',
    "placement_commission_pct" DECIMAL(5,2),
    "tax_terms" VARCHAR(100),
    "client_id" UUID,
    "end_client_id" UUID,
    "end_client_poc_id" UUID,
    "no_of_positions" INTEGER NOT NULL DEFAULT 1,
    "submission_required" INTEGER NOT NULL DEFAULT 5,
    "submission_done" INTEGER NOT NULL DEFAULT 0,
    "urgency" VARCHAR(50) NOT NULL DEFAULT 'WARM',
    "status" VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    "market" VARCHAR(50) NOT NULL DEFAULT 'US',
    "work_mode" VARCHAR(50) DEFAULT 'In Office',
    "start_date" DATE,
    "end_date" DATE,
    "hours_per_week" INTEGER DEFAULT 40,
    "duration" VARCHAR(100),
    "account_manager_id" UUID,
    "recruitment_manager_id" UUID,
    "industry" VARCHAR(100),
    "degree" VARCHAR(100),
    "exp_min" INTEGER DEFAULT 0,
    "exp_max" INTEGER DEFAULT 10,
    "respond_by" DATE,
    "notice_period" VARCHAR(100),
    "approval_status" VARCHAR(50) DEFAULT 'APPROVED',
    "assigned_approver_id" UUID,
    "approved_by" UUID,
    "approved_at" TIMESTAMPTZ(6),
    "rejection_reason" TEXT,
    "job_timezone" VARCHAR(100),
    "shift_timing" VARCHAR(100),
    "deleted_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_co_sourced" BOOLEAN NOT NULL DEFAULT false,
    "margin_split_am_pct" INTEGER,
    "margin_split_rec_pct" INTEGER,
    "shared_branch_ids" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "poc_id" UUID,

    CONSTRAINT "jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."job_delegation_requests" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "job_id" UUID NOT NULL,
    "source_branch_id" UUID NOT NULL,
    "target_branch_id" UUID NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    "sla_days_target" INTEGER,
    "notes" TEXT,
    "assigned_pod_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "source_unit_id" UUID,
    "target_unit_id" UUID,

    CONSTRAINT "job_delegation_requests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."job_pods" (
    "job_id" UUID NOT NULL,
    "pod_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "job_pods_pkey" PRIMARY KEY ("job_id","pod_id")
);

-- CreateTable
CREATE TABLE "ats"."job_assignment_logs" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "job_id" UUID NOT NULL,
    "pod_id" UUID,
    "assigned_by" VARCHAR(255) NOT NULL DEFAULT 'System',
    "assigned_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "job_assignment_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."client_contacts" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "client_id" UUID NOT NULL,
    "created_by" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "designation" VARCHAR(255),
    "email" VARCHAR(255),
    "phone" VARCHAR(50),
    "linkedin_url" VARCHAR(500),
    "is_primary" BOOLEAN NOT NULL DEFAULT false,
    "notes" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "client_contacts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."recruiter_submissions" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "job_id" UUID NOT NULL,
    "candidate_id" UUID NOT NULL,
    "recruiter_id" VARCHAR(255) NOT NULL,
    "l1_status" VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    "l1_date" TIMESTAMPTZ(6),
    "l1_remarks" TEXT,
    "l1_interviewer" VARCHAR(255),
    "l2_status" VARCHAR(50),
    "l2_date" TIMESTAMPTZ(6),
    "l2_remarks" TEXT,
    "l2_interviewer" VARCHAR(255),
    "l3_status" VARCHAR(50),
    "l3_date" TIMESTAMPTZ(6),
    "l3_remarks" TEXT,
    "l3_interviewer" VARCHAR(255),
    "meeting_link" TEXT,
    "final_status" VARCHAR(50) NOT NULL DEFAULT 'SUBMITTED',
    "remarks" TEXT,
    "recruiter_comment" TEXT,
    "pod_lead_remarks" TEXT,
    "review_feedback" TEXT,
    "submitted_rate_amount" DECIMAL(10,2),
    "submitted_rate_currency" VARCHAR(10) DEFAULT 'INR',
    "submitted_rate_term" VARCHAR(50) DEFAULT 'LPA',
    "candidate_current_ctc" DECIMAL(10,2),
    "candidate_expected_ctc" DECIMAL(10,2),
    "candidate_ctc_currency" VARCHAR(10) DEFAULT 'INR',
    "candidate_ctc_term" VARCHAR(50) DEFAULT 'LPA',
    "candidate_notice_period" INTEGER,
    "candidate_relevant_experience" DECIMAL(4,1),
    "candidate_preferred_locations" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "recruiter_submissions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."tenant_stage_remarks" (
    "id" SERIAL NOT NULL,
    "tenant_id" VARCHAR(100) NOT NULL,
    "stage" VARCHAR(50) NOT NULL,
    "remark_text" TEXT NOT NULL,
    "created_by" VARCHAR(100),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "remark_type" VARCHAR(50) DEFAULT 'GENERAL',
    "branch_id" VARCHAR(255),
    "is_global" BOOLEAN DEFAULT true,

    CONSTRAINT "tenant_stage_remarks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."notifications" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "type" VARCHAR(50) NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "message" TEXT NOT NULL,
    "data" JSONB NOT NULL DEFAULT '{}',
    "is_read" BOOLEAN NOT NULL DEFAULT false,
    "initiator_id" VARCHAR(255),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."user_notification_settings" (
    "user_id" UUID NOT NULL,
    "sound_enabled" BOOLEAN NOT NULL DEFAULT true,
    "sound_preset" VARCHAR(50) NOT NULL DEFAULT 'CLASSIC_CHIME',
    "toast_enabled" BOOLEAN NOT NULL DEFAULT true,
    "job_alerts" BOOLEAN NOT NULL DEFAULT true,
    "review_alerts" BOOLEAN NOT NULL DEFAULT true,
    "submission_alerts" BOOLEAN NOT NULL DEFAULT true,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_notification_settings_pkey" PRIMARY KEY ("user_id")
);

-- CreateTable
CREATE TABLE "ats"."audit_logs" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID,
    "actor_id" VARCHAR(255) NOT NULL,
    "actor_email" VARCHAR(255),
    "action" VARCHAR(100) NOT NULL,
    "target_type" VARCHAR(100),
    "target_id" VARCHAR(255),
    "details" JSONB NOT NULL DEFAULT '{}',
    "ip_address" VARCHAR(100),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."bulk_uploads" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "created_by" VARCHAR(255) NOT NULL,
    "total_files" INTEGER NOT NULL DEFAULT 0,
    "processed_files" INTEGER NOT NULL DEFAULT 0,
    "failed_files" INTEGER NOT NULL DEFAULT 0,
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "bulk_uploads_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."bulk_upload_items" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "bulk_upload_id" UUID NOT NULL,
    "filename" VARCHAR(255) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'queued',
    "error_message" TEXT,
    "candidate_id" UUID,
    "candidate_name" VARCHAR(255),
    "candidate_email" VARCHAR(255),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "bulk_upload_items_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."pending_normalizations" (
    "id" SERIAL NOT NULL,
    "category" VARCHAR(50) NOT NULL,
    "raw_value" VARCHAR(255) NOT NULL,
    "detected_count" INTEGER NOT NULL DEFAULT 1,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "pending_normalizations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."skills_master" (
    "id" SERIAL NOT NULL,
    "canonical_name" VARCHAR(255) NOT NULL,
    "category" VARCHAR(100),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "skills_master_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."skill_aliases" (
    "id" SERIAL NOT NULL,
    "skill_id" INTEGER NOT NULL,
    "alias_name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "skill_aliases_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."kv_store" (
    "key" VARCHAR(255) NOT NULL,
    "value" TEXT NOT NULL,
    "updated_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "kv_store_pkey" PRIMARY KEY ("key")
);

-- CreateTable
CREATE TABLE "mass_mail"."email_accounts" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "user_id" VARCHAR(255),
    "tenant_id" UUID,
    "profile_name" VARCHAR(255),
    "provider" VARCHAR(50) NOT NULL,
    "email_address" VARCHAR(255) NOT NULL,
    "access_token" TEXT,
    "refresh_token" TEXT,
    "password" TEXT,
    "smtp_host" VARCHAR(255),
    "smtp_port" INTEGER,
    "imap_host" VARCHAR(255),
    "imap_port" INTEGER,
    "require_ssl" BOOLEAN NOT NULL DEFAULT false,
    "require_tls" BOOLEAN NOT NULL DEFAULT false,
    "is_default" BOOLEAN NOT NULL DEFAULT false,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "shared_with_all" BOOLEAN NOT NULL DEFAULT false,
    "shared_with_branches" UUID[] DEFAULT ARRAY[]::UUID[],
    "shared_with_users" UUID[] DEFAULT ARRAY[]::UUID[],
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "email_accounts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mass_mail"."campaigns" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "subject" VARCHAR(255),
    "body_template" TEXT,
    "status" VARCHAR(50) NOT NULL DEFAULT 'Draft',
    "created_by" UUID,
    "scheduled_at" TIMESTAMPTZ(6),
    "rate_per_minute" INTEGER NOT NULL DEFAULT 0,
    "rate_per_hour" INTEGER NOT NULL DEFAULT 0,
    "randomize_delay" BOOLEAN NOT NULL DEFAULT false,
    "email_account_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "campaigns_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mass_mail"."recipients" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "campaign_id" UUID NOT NULL,
    "candidate_id" UUID,
    "email" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(255),
    "last_name" VARCHAR(255),
    "status" VARCHAR(50) NOT NULL DEFAULT 'Pending',
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "opened_at" TIMESTAMPTZ(6),
    "clicked_at" TIMESTAMPTZ(6),
    "sent_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "recipients_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mass_mail"."email_preferences" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID,
    "action_name" VARCHAR(255) NOT NULL,
    "email_account_id" UUID,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "email_preferences_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mass_mail"."delivery_settings" (
    "tenant_id" UUID NOT NULL,
    "branch_id" VARCHAR(255) NOT NULL DEFAULT 'default',
    "rate_per_minute" INTEGER NOT NULL DEFAULT 30,
    "rate_per_hour" INTEGER NOT NULL DEFAULT 500,
    "randomize_delay" BOOLEAN NOT NULL DEFAULT false,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "delivery_settings_pkey" PRIMARY KEY ("tenant_id","branch_id")
);

-- CreateTable
CREATE TABLE "mass_mail"."templates" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "tenant_id" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "subject" VARCHAR(255),
    "body" TEXT,
    "created_by" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "templates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ats"."_BranchManagers" (
    "A" UUID NOT NULL,
    "B" UUID NOT NULL,

    CONSTRAINT "_BranchManagers_AB_pkey" PRIMARY KEY ("A","B")
);

-- CreateTable
CREATE TABLE "ats"."_BusinessUnitAdmins" (
    "A" UUID NOT NULL,
    "B" UUID NOT NULL,

    CONSTRAINT "_BusinessUnitAdmins_AB_pkey" PRIMARY KEY ("A","B")
);

-- CreateIndex
CREATE UNIQUE INDEX "tenants_domain_key" ON "ats"."tenants"("domain");

-- CreateIndex
CREATE UNIQUE INDEX "tenants_prefix_code_key" ON "ats"."tenants"("prefix_code");

-- CreateIndex
CREATE UNIQUE INDEX "tenant_domains_domain_name_key" ON "ats"."tenant_domains"("domain_name");

-- CreateIndex
CREATE UNIQUE INDEX "tenant_email_domains_email_domain_key" ON "ats"."tenant_email_domains"("email_domain");

-- CreateIndex
CREATE UNIQUE INDEX "branches_tenant_id_name_key" ON "ats"."branches"("tenant_id", "name");

-- CreateIndex
CREATE INDEX "business_units_tenant_id_branch_id_idx" ON "ats"."business_units"("tenant_id", "branch_id");

-- CreateIndex
CREATE UNIQUE INDEX "business_units_tenant_id_branch_id_name_key" ON "ats"."business_units"("tenant_id", "branch_id", "name");

-- CreateIndex
CREATE INDEX "market_segments_tenant_id_idx" ON "ats"."market_segments"("tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "market_segments_tenant_id_code_key" ON "ats"."market_segments"("tenant_id", "code");

-- CreateIndex
CREATE UNIQUE INDEX "market_segments_tenant_id_name_key" ON "ats"."market_segments"("tenant_id", "name");

-- CreateIndex
CREATE UNIQUE INDEX "system_roles_name_key" ON "ats"."system_roles"("name");

-- CreateIndex
CREATE UNIQUE INDEX "system_roles_system_key_key" ON "ats"."system_roles"("system_key");

-- CreateIndex
CREATE UNIQUE INDEX "users_tenant_id_email_key" ON "ats"."users"("tenant_id", "email");

-- CreateIndex
CREATE UNIQUE INDEX "users_tenant_id_keycloak_id_key" ON "ats"."users"("tenant_id", "keycloak_id");

-- CreateIndex
CREATE UNIQUE INDEX "user_invitations_invitation_token_key" ON "ats"."user_invitations"("invitation_token");

-- CreateIndex
CREATE UNIQUE INDEX "user_invitations_tenant_id_email_key" ON "ats"."user_invitations"("tenant_id", "email");

-- CreateIndex
CREATE UNIQUE INDEX "clients_tenant_id_client_code_key" ON "ats"."clients"("tenant_id", "client_code");

-- CreateIndex
CREATE UNIQUE INDEX "jobs_job_code_key" ON "ats"."jobs"("job_code");

-- CreateIndex
CREATE INDEX "idx_tenant_stage_remarks_tenant_branch" ON "ats"."tenant_stage_remarks"("tenant_id", "branch_id", "stage");

-- CreateIndex
CREATE UNIQUE INDEX "pending_normalizations_raw_value_key" ON "ats"."pending_normalizations"("raw_value");

-- CreateIndex
CREATE UNIQUE INDEX "email_accounts_provider_email_address_tenant_id_key" ON "mass_mail"."email_accounts"("provider", "email_address", "tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "email_preferences_action_name_key" ON "mass_mail"."email_preferences"("action_name");

-- CreateIndex
CREATE INDEX "_BranchManagers_B_index" ON "ats"."_BranchManagers"("B");

-- CreateIndex
CREATE INDEX "_BusinessUnitAdmins_B_index" ON "ats"."_BusinessUnitAdmins"("B");

-- AddForeignKey
ALTER TABLE "ats"."job_recruiters" ADD CONSTRAINT "job_recruiters_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "ats"."jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_recruiters" ADD CONSTRAINT "job_recruiters_recruiter_id_fkey" FOREIGN KEY ("recruiter_id") REFERENCES "ats"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."tenant_counters" ADD CONSTRAINT "tenant_counters_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."tenant_domains" ADD CONSTRAINT "tenant_domains_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."tenant_auth_settings" ADD CONSTRAINT "tenant_auth_settings_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."tenant_email_domains" ADD CONSTRAINT "tenant_email_domains_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."tenant_dice_integrations" ADD CONSTRAINT "tenant_dice_integrations_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."branches" ADD CONSTRAINT "branches_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."business_units" ADD CONSTRAINT "business_units_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."business_units" ADD CONSTRAINT "business_units_market_segment_id_fkey" FOREIGN KEY ("market_segment_id") REFERENCES "ats"."market_segments"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."business_units" ADD CONSTRAINT "business_units_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."market_segments" ADD CONSTRAINT "market_segments_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."custom_roles" ADD CONSTRAINT "custom_roles_base_role_id_fkey" FOREIGN KEY ("base_role_id") REFERENCES "ats"."custom_roles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."custom_roles" ADD CONSTRAINT "custom_roles_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."custom_roles" ADD CONSTRAINT "custom_roles_business_unit_id_fkey" FOREIGN KEY ("business_unit_id") REFERENCES "ats"."business_units"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."custom_roles" ADD CONSTRAINT "custom_roles_system_role_id_fkey" FOREIGN KEY ("system_role_id") REFERENCES "ats"."system_roles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."custom_roles" ADD CONSTRAINT "custom_roles_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."pods" ADD CONSTRAINT "pods_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."pods" ADD CONSTRAINT "pods_business_unit_id_fkey" FOREIGN KEY ("business_unit_id") REFERENCES "ats"."business_units"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."pods" ADD CONSTRAINT "pods_pod_head_id_fkey" FOREIGN KEY ("pod_head_id") REFERENCES "ats"."users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."pods" ADD CONSTRAINT "pods_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_business_unit_id_fkey" FOREIGN KEY ("business_unit_id") REFERENCES "ats"."business_units"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_job_reviewer_id_fkey" FOREIGN KEY ("job_reviewer_id") REFERENCES "ats"."users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_pod_id_fkey" FOREIGN KEY ("pod_id") REFERENCES "ats"."pods"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "ats"."custom_roles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."users" ADD CONSTRAINT "users_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_invitations" ADD CONSTRAINT "user_invitations_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_invitations" ADD CONSTRAINT "user_invitations_pod_id_fkey" FOREIGN KEY ("pod_id") REFERENCES "ats"."pods"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_invitations" ADD CONSTRAINT "user_invitations_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "ats"."custom_roles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_invitations" ADD CONSTRAINT "user_invitations_system_role_id_fkey" FOREIGN KEY ("system_role_id") REFERENCES "ats"."system_roles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_invitations" ADD CONSTRAINT "user_invitations_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."clients" ADD CONSTRAINT "clients_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."clients" ADD CONSTRAINT "clients_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."candidates" ADD CONSTRAINT "candidates_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."candidates" ADD CONSTRAINT "candidates_resume_record_id_fkey" FOREIGN KEY ("resume_record_id") REFERENCES "ats"."resumes"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."candidates" ADD CONSTRAINT "candidates_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_branch_id_fkey" FOREIGN KEY ("branch_id") REFERENCES "ats"."branches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "ats"."clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_end_client_id_fkey" FOREIGN KEY ("end_client_id") REFERENCES "ats"."clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_poc_id_fkey" FOREIGN KEY ("poc_id") REFERENCES "ats"."client_contacts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."jobs" ADD CONSTRAINT "jobs_end_client_poc_id_fkey" FOREIGN KEY ("end_client_poc_id") REFERENCES "ats"."client_contacts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_assigned_pod_id_fkey" FOREIGN KEY ("assigned_pod_id") REFERENCES "ats"."pods"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "ats"."jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_source_branch_id_fkey" FOREIGN KEY ("source_branch_id") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_source_unit_id_fkey" FOREIGN KEY ("source_unit_id") REFERENCES "ats"."business_units"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_target_branch_id_fkey" FOREIGN KEY ("target_branch_id") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_target_unit_id_fkey" FOREIGN KEY ("target_unit_id") REFERENCES "ats"."business_units"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_delegation_requests" ADD CONSTRAINT "job_delegation_requests_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_pods" ADD CONSTRAINT "job_pods_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "ats"."jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_pods" ADD CONSTRAINT "job_pods_pod_id_fkey" FOREIGN KEY ("pod_id") REFERENCES "ats"."pods"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_assignment_logs" ADD CONSTRAINT "job_assignment_logs_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "ats"."jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_assignment_logs" ADD CONSTRAINT "job_assignment_logs_pod_id_fkey" FOREIGN KEY ("pod_id") REFERENCES "ats"."pods"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."job_assignment_logs" ADD CONSTRAINT "job_assignment_logs_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."client_contacts" ADD CONSTRAINT "client_contacts_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "ats"."clients"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."client_contacts" ADD CONSTRAINT "client_contacts_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "ats"."users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."client_contacts" ADD CONSTRAINT "client_contacts_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."recruiter_submissions" ADD CONSTRAINT "recruiter_submissions_candidate_id_fkey" FOREIGN KEY ("candidate_id") REFERENCES "ats"."candidates"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."recruiter_submissions" ADD CONSTRAINT "recruiter_submissions_job_id_fkey" FOREIGN KEY ("job_id") REFERENCES "ats"."jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."recruiter_submissions" ADD CONSTRAINT "recruiter_submissions_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."notifications" ADD CONSTRAINT "notifications_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."notifications" ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "ats"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."user_notification_settings" ADD CONSTRAINT "user_notification_settings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "ats"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."audit_logs" ADD CONSTRAINT "audit_logs_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."bulk_uploads" ADD CONSTRAINT "bulk_uploads_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "ats"."tenants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."bulk_upload_items" ADD CONSTRAINT "bulk_upload_items_bulk_upload_id_fkey" FOREIGN KEY ("bulk_upload_id") REFERENCES "ats"."bulk_uploads"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."bulk_upload_items" ADD CONSTRAINT "bulk_upload_items_candidate_id_fkey" FOREIGN KEY ("candidate_id") REFERENCES "ats"."candidates"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."skill_aliases" ADD CONSTRAINT "skill_aliases_skill_id_fkey" FOREIGN KEY ("skill_id") REFERENCES "ats"."skills_master"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mass_mail"."campaigns" ADD CONSTRAINT "campaigns_email_account_id_fkey" FOREIGN KEY ("email_account_id") REFERENCES "mass_mail"."email_accounts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mass_mail"."recipients" ADD CONSTRAINT "recipients_campaign_id_fkey" FOREIGN KEY ("campaign_id") REFERENCES "mass_mail"."campaigns"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mass_mail"."email_preferences" ADD CONSTRAINT "email_preferences_email_account_id_fkey" FOREIGN KEY ("email_account_id") REFERENCES "mass_mail"."email_accounts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."_BranchManagers" ADD CONSTRAINT "_BranchManagers_A_fkey" FOREIGN KEY ("A") REFERENCES "ats"."branches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."_BranchManagers" ADD CONSTRAINT "_BranchManagers_B_fkey" FOREIGN KEY ("B") REFERENCES "ats"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."_BusinessUnitAdmins" ADD CONSTRAINT "_BusinessUnitAdmins_A_fkey" FOREIGN KEY ("A") REFERENCES "ats"."business_units"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ats"."_BusinessUnitAdmins" ADD CONSTRAINT "_BusinessUnitAdmins_B_fkey" FOREIGN KEY ("B") REFERENCES "ats"."users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
