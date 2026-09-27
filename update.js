const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', 'utf8');

const newUI = fs.readFileSync('new_ui.txt', 'utf8');

// Add state property
code = code.replace(/roleId: "",/, 'roleCategory: "",\n      roleId: "",');

// Add state init in openReviewModal
code = code.replace(/roles: user\.requestedRole \? \[user\.requestedRole\] : \(user\.roles \|\| \[\]\),/g, 'roles: user.requestedRole ? [user.requestedRole] : (user.roles || []),\n        roleCategory: isReqTenant ? "TENANT_ADMIN" : isReqBranchAdmin ? "BRANCH_ADMIN" : (reqUpper === "UNIT_ADMIN" || reqUpper === "UNIT ADMIN") ? "UNIT_ADMIN" : "EMPLOYEE",');

const startTag = '{/* Form Controls */}';
const endTag = '{/* Modal Footer */}';

const startIndex = code.indexOf(startTag);
const endIndex = code.indexOf(endTag);

if(startIndex !== -1 && endIndex !== -1) {
    code = code.substring(0, startIndex) + newUI + '\n              ' + code.substring(endIndex);
    fs.writeFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', code);
    console.log('Successfully updated modal UI');
} else {
    console.log('Could not find modal tags');
}
