const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', 'utf8');

const addModalIdx = code.indexOf('isAddModalOpen &&');
const searchLabel = 'Office Branch <span className="text-red-500">*</span>';
const branchLabelIdx = code.indexOf(searchLabel, addModalIdx);
const start = code.lastIndexOf('<div className="space-y-1', branchLabelIdx);

console.log(code.substring(addModalIdx, start));
