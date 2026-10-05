const fs = require('fs');
const file = 'ats_frontend_main/components/auth/login-form.tsx';
let content = fs.readFileSync(file, 'utf8');

const regex1 = /if \(userSub && !isMasterTenant\) \{[\s\S]*?\} else if \(isMasterTenant && !currentSub\) \{/m;
const replacement1 = `if (userSub && !isMasterTenant) {
              const isPlatformOwnerOnRoot = (userSub === "enfycon" || userSub === "enfy") && currentSub === "";
              if (currentSub === userSub || isPlatformOwnerOnRoot) {
                window.location.replace("/dashboard");
              } else if (!currentSub) {
                signOut({ redirect: false });
              }
            } else if (isMasterTenant && !currentSub) {`;

content = content.replace(regex1, replacement1);

const regex2 = /if \(userTenantDomain && !isMasterTenant && currentSubdomain !== userTenantDomain\) \{/m;
const replacement2 = `const isPlatformOwnerOnRoot = (userTenantDomain === "enfycon" || userTenantDomain === "enfy") && currentSubdomain === "";
        if (userTenantDomain && !isMasterTenant && currentSubdomain !== userTenantDomain && !isPlatformOwnerOnRoot) {`;

content = content.replace(regex2, replacement2);

fs.writeFileSync(file, content);
