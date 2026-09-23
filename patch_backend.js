const fs = require('fs');

// Patch auth-tenant.service.ts
let serviceCode = fs.readFileSync('ats_backend/src/auth/services/auth-tenant.service.ts', 'utf8');

const serviceSignatureEnd = serviceCode.indexOf('enforceJobCodePattern?: boolean;\n  }) {');
if (serviceSignatureEnd > -1) {
  serviceCode = serviceCode.replace(
    'enforceJobCodePattern?: boolean;\n  }) {',
    'enforceJobCodePattern?: boolean;\n    siteTitle?: string;\n    logoUrl?: string;\n    name?: string;\n  }) {'
  );
}

const serviceSqlEnd = serviceCode.indexOf('if (fields.length === 0)');
if (serviceSqlEnd > -1) {
  const newLines = `    if (settings.siteTitle !== undefined) { fields.push(\`site_title = $\${paramIndex}\`); params.push(settings.siteTitle); paramIndex++; }
    if (settings.logoUrl !== undefined) { fields.push(\`logo_url = $\${paramIndex}\`); params.push(settings.logoUrl); paramIndex++; }
    if (settings.name !== undefined) { fields.push(\`name = $\${paramIndex}\`); params.push(settings.name); paramIndex++; }

    `;
  serviceCode = serviceCode.substring(0, serviceSqlEnd) + newLines + serviceCode.substring(serviceSqlEnd);
}

fs.writeFileSync('ats_backend/src/auth/services/auth-tenant.service.ts', serviceCode, 'utf8');


// Patch auth.controller.ts
let controllerCode = fs.readFileSync('ats_backend/src/auth/auth.controller.ts', 'utf8');

const controllerSignatureEnd = controllerCode.indexOf('enforceJobCodePattern?: boolean;\n    },\n  ) {');
if (controllerSignatureEnd > -1) {
  controllerCode = controllerCode.replace(
    'enforceJobCodePattern?: boolean;\n    },\n  ) {',
    'enforceJobCodePattern?: boolean;\n      siteTitle?: string;\n      logoUrl?: string;\n      name?: string;\n    },\n  ) {'
  );
}
fs.writeFileSync('ats_backend/src/auth/auth.controller.ts', controllerCode, 'utf8');

console.log('Successfully patched backend service and controller');
