const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', 'utf8');

const wrongEditSelectRegex = /[\s]*\{\/\* Business Unit Selection \*\/\}\s*<div className="space-y-1 mb-4">\s*<label className="text-xs font-bold text-neutral-700 dark:text-neutral-300">Target Business Unit \(Optional\)<\/label>\s*<select\s*value=\{editForm\.businessUnitId\}[\s\S]*?<\/select>\s*<\/div>/;

const editModalStart = code.indexOf('isEditModalOpen &&');
const officeBranchIdx = code.indexOf('Office Branch *', editModalStart);
const selectEnd = code.indexOf('</select>', officeBranchIdx);
const divEnd = code.indexOf('</div>', selectEnd) + 6;

// Check if it's already moved (in case of retry)
const editModalSection = code.substring(editModalStart, divEnd + 1000);
if (!editModalSection.includes('editForm.businessUnitId')) {
    const match = code.match(wrongEditSelectRegex);
    if (match) {
        const block = match[0].replace('Target Business Unit', 'Branch Unit');
        
        // Remove from wrong place
        code = code.replace(wrongEditSelectRegex, '');
        
        // Find the new insertion point (we recalculate since we removed text before it)
        const newEditModalStart = code.indexOf('isEditModalOpen &&');
        const newOfficeBranchIdx = code.indexOf('Office Branch *', newEditModalStart);
        const newSelectEnd = code.indexOf('</select>', newOfficeBranchIdx);
        // Wait, the select is conditionally rendered. Let's find the closing `</div>` of the space-y-1 div containing Office Branch.
        // It's the one before `/* CUSTOM ROLE SELECTION`
        const customRoleIdx = code.indexOf('{/* CUSTOM ROLE SELECTION', newOfficeBranchIdx);
        
        code = code.substring(0, customRoleIdx) + block + '\n\n              ' + code.substring(customRoleIdx);
        
        // Also fix the Add Modal's label
        code = code.replace(/<label className="text-xs font-bold text-neutral-700 dark:text-neutral-300">Target Business Unit \(Optional\)<\/label>/g, '<label className="text-xs font-bold text-neutral-700 dark:text-neutral-300">Branch Unit (Optional)</label>');
        
        fs.writeFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', code, 'utf8');
        console.log('Moved Business Unit select to Edit Modal successfully!');
    } else {
        console.log('Could not find the misplaced block to move.');
    }
} else {
    console.log('It seems editForm.businessUnitId is already in the edit modal.');
}
