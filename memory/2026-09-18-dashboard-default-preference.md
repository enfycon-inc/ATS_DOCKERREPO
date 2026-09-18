# Dashboard default preference

Requested rule: remember the user's last selected dashboard; first login uses their configured primary role.

Removed backend ranking from profile and user-list role selection, using users.role_id and preserving it on role edits when still assigned. The role permission union is unchanged. Added browser persistence keyed by tenant and user, kept across logout. All four dashboard/navigation consumers read this scoped preference; only currently assigned roles can resolve it. No saved choice or a removed choice falls back to primary. Persistence is browser-local, not cross-device. No database assignments were modified.

Regression coverage includes a BDM primary alongside Branch Admin, retained permission union, account/workspace isolation, session cleanup, revoked preference fallback, and existing no-reload switching behavior. Deployment and authenticated live-site verification remain separate.
