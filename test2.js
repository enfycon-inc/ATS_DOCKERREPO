const fs = require('fs');
let code = fs.readFileSync('ats_backend/src/auth/services/auth-user.service.ts', 'utf8');
const start = code.indexOf('async requestRole(');
const end = code.indexOf('async approveTenantUser(');
const replaceStr = \sync requestRole(userId: string, role: string, branchId?: string, businessUnitId?: string) {
      const userRes = await this.authQuery.query(
        'SELECT id, email, full_name, tenant_id FROM users WHERE id =  LIMIT 1',
        [userId]
      );
      if (userRes.rows.length === 0) throw new NotFoundException('User not found.');
  
      await this.authQuery.query(
        'UPDATE users SET requested_role = , branch_id = ::uuid, business_unit_id = ::uuid, updated_at = NOW() WHERE id = ::uuid',
        [role, branchId || null, businessUnitId || null, userId]
      );

      try {
        const adminsRes = await this.authQuery.query(
          "SELECT u.id FROM users u INNER JOIN custom_roles cr ON u.role_id = cr.id INNER JOIN system_roles sr ON cr.system_role_id = sr.id WHERE u.tenant_id =  AND sr.system_key IN ('ADMIN', 'SUPER_ADMIN') AND u.is_active = true",
          [userRes.rows[0].tenant_id]
        );
        if (adminsRes.rows.length > 0) {
          const title = 'New Role Request';
          const msg = \\ requested the \ role.\;
          for (const admin of adminsRes.rows) {
            await this.authQuery.query(
              "INSERT INTO notifications (tenant_id, user_id, type, title, message, data, is_read, initiator_id, created_at) VALUES (, , 'ROLE_REQUEST', , , '{}'::jsonb, false, , NOW())",
              [userRes.rows[0].tenant_id, admin.id, title, msg, userId]
            );
          }
        }
      } catch (err) {}

      return { success: true, message: 'Role request submitted for approval.' };
    }

    \;
code = code.substring(0, start) + replaceStr + code.substring(end);
fs.writeFileSync('ats_backend/src/auth/services/auth-user.service.ts', code);
