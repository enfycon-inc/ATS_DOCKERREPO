const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', 'utf8');

// 1. Add setCompanyName to TenantAdminSettingsView
const tenantAdminStart = code.indexOf('<TenantAdminSettingsView');
const companyNameProp = 'companyName={companyName}';
if (code.includes(companyNameProp)) {
  code = code.replace(companyNameProp, 'companyName={companyName}\n          setCompanyName={setCompanyName}');
} else {
  console.log('Could not find companyName={companyName} inside TenantAdminSettingsView');
}

// 2. Replace <GeneralTab /> inside TenantAdminSettingsView
const generalTabStart = code.indexOf('<GeneralTab');
const generalTabEnd = code.indexOf('/>', generalTabStart) + 2;

const newGeneralTab = `<GeneralTab
            companyName={props.companyName}
            setCompanyName={props.setCompanyName}
            subdomain={props.subdomain}
            setSubdomain={props.setSubdomain}
            originalSubdomain={props.originalSubdomain}
            savingSubdomain={props.savingSubdomain}
            handleSaveSubdomain={props.handleSaveSubdomain}
            isSuperAdmin={props.isSuperAdmin}
            base={base}
          />`;

code = code.substring(0, generalTabStart) + newGeneralTab + code.substring(generalTabEnd);

// 3. Remove the unused import interfaces from general-tab.tsx import
code = code.replace('import { GeneralTab, BranchItem, BusinessUnitItem } from "@/components/company/tabs/general-tab";', 'import { GeneralTab } from "@/components/company/tabs/general-tab";');

// 4. We must define the dummy interfaces inside company/page.tsx so that the state declarations compile
const dummyInterfaces = `
export interface BranchItem { id: string; name: string; code: string; location: string; status: string; unitsCount: number; staffCount: number; reqsCount: number; }
export interface BusinessUnitItem { id: string; branchId: string; name: string; code: string; market: string; shiftTiming: string; staffCount: number; reqsCount: number; status: string; }
`;

const importEnd = code.indexOf('export default function CompanySettingsPage');
code = code.substring(0, importEnd) + dummyInterfaces + '\n' + code.substring(importEnd);


fs.writeFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', code, 'utf8');
console.log('Successfully patched company/page.tsx');
