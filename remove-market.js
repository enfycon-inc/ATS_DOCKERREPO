const fs = require('fs');
const file = 'ats_frontend_main/app/(dashboard)/utility/approvals/page.tsx';
let content = fs.readFileSync(file, 'utf8');

const regex = /<div className="space-y-1">\s*<label className="text-xs font-bold text-default-800">Default Staffing Market<\/label>[\s\S]*?Indian Staffing\s*<\/button>\s*<\/div>\s*<\/div>/;

content = content.replace(regex, "");

fs.writeFileSync(file, content);
