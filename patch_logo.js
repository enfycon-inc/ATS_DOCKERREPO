const fs = require('fs');

// Patch general-tab.tsx
let generalTabCode = fs.readFileSync('ats_frontend_main/components/company/tabs/general-tab.tsx', 'utf8');

// Add props
generalTabCode = generalTabCode.replace(
  'siteTitle: string;\n  setSiteTitle: (val: string) => void;',
  'siteTitle: string;\n  setSiteTitle: (val: string) => void;\n  logoUrl: string;\n  setLogoUrl: (val: string) => void;\n  handleSaveCompanyProfile: () => void;\n  savingCompanyProfile: boolean;'
);

generalTabCode = generalTabCode.replace(
  'siteTitle,\n  setSiteTitle,',
  'siteTitle,\n  setSiteTitle,\n  logoUrl,\n  setLogoUrl,\n  handleSaveCompanyProfile,\n  savingCompanyProfile,'
);

// Replace Logo Area
const logoStart = generalTabCode.indexOf('<div className="w-28 h-28 border-2 border-dashed border-neutral-300 dark:border-slate-700 rounded-xl flex flex-col items-center justify-center bg-neutral-50 dark:bg-slate-800/50 hover:bg-neutral-100 dark:hover:bg-slate-800 transition-colors cursor-pointer overflow-hidden group">');
const logoEndStr = '</div>\n            </div>';
const logoEnd = generalTabCode.indexOf(logoEndStr, logoStart) + '</div>'.length;

const newLogoArea = `<div 
                onClick={() => document.getElementById('logo-upload')?.click()}
                className="relative w-28 h-28 border-2 border-dashed border-neutral-300 dark:border-slate-700 rounded-xl flex flex-col items-center justify-center bg-neutral-50 dark:bg-slate-800/50 hover:bg-neutral-100 dark:hover:bg-slate-800 transition-colors cursor-pointer overflow-hidden group"
              >
                <input 
                  id="logo-upload"
                  type="file" 
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        setLogoUrl(reader.result as string);
                      };
                      reader.readAsDataURL(file);
                    }
                  }}
                />
                {logoUrl ? (
                  <img src={logoUrl} alt="Company Logo" className="w-full h-full object-contain p-2" />
                ) : (
                  <>
                    <ImageIcon className="h-8 w-8 text-neutral-400 group-hover:text-indigo-500 transition-colors mb-2" />
                    <span className="text-[10px] font-medium text-neutral-500 group-hover:text-indigo-600">Upload Logo</span>
                  </>
                )}
              </div>`;

generalTabCode = generalTabCode.substring(0, logoStart) + newLogoArea + generalTabCode.substring(logoEnd);

// Replace Button
const btnStart = generalTabCode.indexOf('<Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold h-9">');
const btnEndStr = '</Button>';
const btnEnd = generalTabCode.indexOf(btnEndStr, btnStart) + btnEndStr.length;

const newBtn = `<Button 
                  size="sm" 
                  onClick={handleSaveCompanyProfile}
                  disabled={savingCompanyProfile}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold h-9"
                >
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  {savingCompanyProfile ? "Saving..." : "Save Company Profile"}
                </Button>`;

generalTabCode = generalTabCode.substring(0, btnStart) + newBtn + generalTabCode.substring(btnEnd);

fs.writeFileSync('ats_frontend_main/components/company/tabs/general-tab.tsx', generalTabCode, 'utf8');
console.log('Successfully patched general-tab.tsx');

// Patch company/page.tsx
let pageCode = fs.readFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', 'utf8');

// Add logoUrl and savingCompanyProfile state
const stateInsertIdx = pageCode.indexOf('const [siteTitle, setSiteTitle] = useState("");');
if (stateInsertIdx > -1) {
  const insertStr = 'const [siteTitle, setSiteTitle] = useState("");\n    const [logoUrl, setLogoUrl] = useState("");\n    const [savingCompanyProfile, setSavingCompanyProfile] = useState(false);';
  pageCode = pageCode.replace('const [siteTitle, setSiteTitle] = useState("");', insertStr);
}

// Add handleSaveCompanyProfile function
const handleSaveInsertIdx = pageCode.indexOf('const handleSaveSubdomain = async (e: React.FormEvent) => {');
if (handleSaveInsertIdx > -1) {
  const newHandler = `
  const handleSaveCompanyProfile = async () => {
    try {
      setSavingCompanyProfile(true);
      await atsApi.auth.updateMySettings({ 
        name: companyName,
        siteTitle: siteTitle,
        logoUrl: logoUrl
      });
      toast.success("Company profile saved successfully!");
    } catch (err: any) {
      toast.error(err.message || "Failed to save company profile");
    } finally {
      setSavingCompanyProfile(false);
    }
  };

  `;
  pageCode = pageCode.substring(0, handleSaveInsertIdx) + newHandler + pageCode.substring(handleSaveInsertIdx);
}

// Add to TenantAdminSettingsView props call
pageCode = pageCode.replace(
  'siteTitle={siteTitle}\n            setSiteTitle={setSiteTitle}',
  'siteTitle={siteTitle}\n            setSiteTitle={setSiteTitle}\n            logoUrl={logoUrl}\n            setLogoUrl={setLogoUrl}\n            savingCompanyProfile={savingCompanyProfile}\n            handleSaveCompanyProfile={handleSaveCompanyProfile}'
);

// Add to GeneralTab inside TenantAdminSettingsView
pageCode = pageCode.replace(
  'siteTitle={props.siteTitle}\n            setSiteTitle={props.setSiteTitle}',
  'siteTitle={props.siteTitle}\n            setSiteTitle={props.setSiteTitle}\n            logoUrl={props.logoUrl}\n            setLogoUrl={props.setLogoUrl}\n            savingCompanyProfile={props.savingCompanyProfile}\n            handleSaveCompanyProfile={props.handleSaveCompanyProfile}'
);

fs.writeFileSync('ats_frontend_main/app/(dashboard)/company/page.tsx', pageCode, 'utf8');
console.log('Successfully patched company/page.tsx');
