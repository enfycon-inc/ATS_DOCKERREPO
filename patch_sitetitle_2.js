const fs = require('fs');

let pageCode = fs.readFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', 'utf8');

const tenantAdminInsertIdx = pageCode.indexOf('companyName={companyName}');
if (tenantAdminInsertIdx > -1) {
  // It currently has: companyName={companyName}\n            setCompanyName={setCompanyName}
  pageCode = pageCode.replace(
    'companyName={companyName}\n            setCompanyName={setCompanyName}',
    'companyName={companyName}\n            setCompanyName={setCompanyName}\n            siteTitle={siteTitle}\n            setSiteTitle={setSiteTitle}'
  );
}

fs.writeFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', pageCode, 'utf8');
console.log('Successfully patched company/page.tsx');
