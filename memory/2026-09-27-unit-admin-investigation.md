# Unit Admin sidebar and office label investigation

Scope: investigation requested; no application code, account assignments, or database records changed.

Symptoms: screenshot shows Unit Admin label with tenant-wide admin widgets and admin navigation, plus Office: Assigned Office.

Confirmed findings:
- navbar-right.tsx BranchSwitcher persists user.branchName || 'Assigned Office' when enforcing the assigned branch. It trusts the saved name on subsequent mounts. Its fresh getProfile request updates city/unit only, never branchName. Missing cached branchName can therefore leave a permanent placeholder even when the profile later has the name.
- role-permissions.ts has hardcoded role navigation and permission defaults. getFilteredMoreNav allows company/SSO via isAdmin without checking explicit capabilities. getActiveRolePermissions ignores an explicitly empty role permissions array and substitutes a hardcoded permission bundle.
- A Node reproduction using transpiled repository functions confirmed a role named Unit Admin with systemRole ADMIN and only unit_admin:manage exposes company/SSO and the admin navigation. The same role mapped to UNIT_ADMIN hides company/SSO, Branch and Markets; Branch & Units remains with Units only.
- Role lookup uses the first matching name or ID; sidebar supplies active.name, permitting ambiguity when names are duplicated.
- Dashboard page renders tenant admin widgets for ADMIN/TENANT_ADMIN. It has no UNIT_ADMIN branch, so correctly resolved UNIT_ADMIN falls through to recruiter widgets. Thus the screenshot's tenant dashboard is not the current default for UNIT_ADMIN.
- No hardcoded target email found in searched backend source and frontend lib/components.

Root cause hypothesis for live account: incorrect role system mapping, ambiguous catalog name resolution, or deployed code differing from this workspace. This remains unconfirmed. The configured database read-only lookup returned no row for the supplied email. Do not infer that the production account is absent.

Evidence: isolated function execution reproduced role-based menu bypass and empty-permission fallback. Static data-flow inspection confirmed persistent office placeholder. No production browser verification performed; no fixes or regression tests added. Prior memory documents related role selection and sidebar issues, with deployment not verified.

Status: investigation completed with live-account verification limitation. A fix should remove role-based authorization/default grants, preserve exact assigned role identity, refresh branch context from the authoritative profile, and give Unit Admin an explicitly scoped dashboard. Verify live role mapping before changing account data.
