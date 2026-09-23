const fs = require('fs');

// --- Patch general-tab.tsx ---
let generalTabCode = fs.readFileSync('ats_frontend_main/components/company/tabs/general-tab.tsx', 'utf8');

// Update Interface
generalTabCode = generalTabCode.replace(
  'companyName: string;\n  setCompanyName: (val: string) => void;',
  'companyName: string;\n  setCompanyName: (val: string) => void;\n  siteTitle: string;\n  setSiteTitle: (val: string) => void;'
);

// Update Component signature
generalTabCode = generalTabCode.replace(
  'companyName,\n  setCompanyName,\n  subdomain,',
  'companyName,\n  setCompanyName,\n  siteTitle,\n  setSiteTitle,\n  subdomain,'
);

// Replace the form fields
const startDiv = `              <div>
                <Label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">Company Name</Label>`;
const endDiv = `                  </select>
                </div>
              </div>`;

const newFields = `              <div className="space-y-4">
                <div>
                  <Label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">Company Name</Label>
                  <Input
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g. Enfycon Inc."
                    className="h-9 mt-1.5 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">Browser Site Title</Label>
                  <Input
                    value={siteTitle}
                    onChange={(e) => setSiteTitle(e.target.value)}
                    placeholder="e.g. Enfycon ATS"
                    className="h-9 mt-1.5 text-sm"
                  />
                  <p className="text-[10px] text-neutral-500 mt-1">This appears on browser tabs and search engines.</p>
                </div>
              </div>`;

const formStartIdx = generalTabCode.indexOf(startDiv);
const formEndIdx = generalTabCode.indexOf(endDiv) + endDiv.length;

if (formStartIdx > -1 && formEndIdx > -1) {
  generalTabCode = generalTabCode.substring(0, formStartIdx) + newFields + generalTabCode.substring(formEndIdx);
  fs.writeFileSync('ats_frontend_main/components/company/tabs/general-tab.tsx', generalTabCode, 'utf8');
  console.log('Successfully patched general-tab.tsx');
} else {
  console.log('Failed to find form fields in general-tab.tsx');
}


// --- Patch company/page.tsx ---
let pageCode = fs.readFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', 'utf8');

// Add state to CompanySettingsContent
const stateInsertIdx = pageCode.indexOf('const [companyName, setCompanyName] = useState("");');
if (stateInsertIdx > -1) {
  const insertStr = 'const [companyName, setCompanyName] = useState("");\n    const [siteTitle, setSiteTitle] = useState("");';
  pageCode = pageCode.replace('const [companyName, setCompanyName] = useState("");', insertStr);
}

// Pass state to TenantAdminSettingsView
const tenantAdminInsertIdx = pageCode.indexOf('companyName={companyName}');
if (tenantAdminInsertIdx > -1) {
  pageCode = pageCode.replace(
    'companyName={companyName}\n            setCompanyName={setCompanyName}',
    'companyName={companyName}\n            setCompanyName={setCompanyName}\n            siteTitle={siteTitle}\n            setSiteTitle={setSiteTitle}'
  );
}

// Update GeneralTab props inside TenantAdminSettingsView
const generalTabInsertIdx = pageCode.indexOf('companyName={props.companyName}');
if (generalTabInsertIdx > -1) {
  pageCode = pageCode.replace(
    'companyName={props.companyName}\n            setCompanyName={props.setCompanyName}',
    'companyName={props.companyName}\n            setCompanyName={props.setCompanyName}\n            siteTitle={props.siteTitle}\n            setSiteTitle={props.setSiteTitle}'
  );
}

fs.writeFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', pageCode, 'utf8');
console.log('Successfully patched company/page.tsx');
