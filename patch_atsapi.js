const fs = require('fs');

let apiCode = fs.readFileSync('ats_frontend_main/lib/ats-api.ts', 'utf8');

const apiSignatureEnd = apiCode.indexOf('enforceJobCodePattern?: boolean;\n  }): Promise<any> {');
if (apiSignatureEnd > -1) {
  apiCode = apiCode.replace(
    'enforceJobCodePattern?: boolean;\n  }): Promise<any> {',
    'enforceJobCodePattern?: boolean;\n    siteTitle?: string;\n    logoUrl?: string;\n    name?: string;\n  }): Promise<any> {'
  );
}

fs.writeFileSync('ats_frontend_main/lib/ats-api.ts', apiCode, 'utf8');
console.log('Successfully patched ats-api.ts');
