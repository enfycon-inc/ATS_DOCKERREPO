const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', 'utf8');

function replaceBlock(isEdit) {
    const branchVar = isEdit ? 'editForm.branchId' : 'addForm.branchId';
    const unitVar = isEdit ? 'editForm.businessUnitId' : 'addForm.businessUnitId';
    
    const branchLabelStr = isEdit ? 'Office Branch *' : 'Office Branch <span className="text-red-500">*</span>';
    const unitLabelStr = isEdit ? 'Branch Unit (Optional)' : 'Target Business Unit (Optional)';
    
    // Find the branch block
    let idx = 0;
    while(true) {
        idx = code.indexOf(branchLabelStr, idx + 1);
        if (idx === -1) return false;
        
        // Ensure it's the correct one by checking the variable
        const nextPart = code.substring(idx, idx + 1000);
        if (nextPart.includes(branchVar)) {
            break;
        }
    }
    
    const branchStart = code.lastIndexOf('<div className="space-y-1', idx);
    const selectEnd = code.indexOf('</select>', branchStart);
    const branchEnd = code.indexOf('</div>', selectEnd) + 6;
    
    // Find the unit block
    const unitLabelIdx = code.indexOf(unitLabelStr, branchEnd);
    const unitStart = code.lastIndexOf('<div className="space-y-1', unitLabelIdx);
    const unitSelectEnd = code.indexOf('</select>', unitStart);
    const unitEnd = code.indexOf('</div>', unitSelectEnd) + 6;
    
    const branchBlock = code.substring(branchStart, branchEnd);
    const unitBlock = code.substring(unitStart, unitEnd);
    
    // We will extract these two blocks and wrap them.
    // Wait, the branch block might have `pt-2 border-t` or similar. Let's remove them from the inner branch block and put it on the wrapper.
    let cleanBranchBlock = branchBlock;
    let wrapperClasses = 'grid grid-cols-1 sm:grid-cols-2 gap-3';
    
    const borderMatch = branchBlock.match(/<div className="space-y-1([^"]+)"/);
    if (borderMatch) {
        wrapperClasses += borderMatch[1]; // append things like ' pt-2 border-t...'
        cleanBranchBlock = cleanBranchBlock.replace(borderMatch[0], '<div className="space-y-1"');
    }
    
    let cleanUnitBlock = unitBlock;
    const mbMatch = unitBlock.match(/<div className="space-y-1([^"]+)"/);
    if (mbMatch) {
        cleanUnitBlock = cleanUnitBlock.replace(mbMatch[0], '<div className="space-y-1"');
    }
    
    // Replace "Target Business Unit" with "Branch Unit" for consistency in both
    cleanUnitBlock = cleanUnitBlock.replace('Target Business Unit', 'Branch Unit');
    
    const wrapped = `<div className="${wrapperClasses}">
${cleanBranchBlock}
${cleanUnitBlock}
</div>`;

    // Now remove the unitBlock from its original position
    code = code.substring(0, unitStart) + code.substring(unitEnd);
    
    // Replace the branchBlock with the wrapped block
    const newBranchStart = code.indexOf(branchBlock);
    code = code.substring(0, newBranchStart) + wrapped + code.substring(newBranchStart + branchBlock.length);
    
    return true;
}

replaceBlock(false); // Add Modal
replaceBlock(true);  // Edit Modal

fs.writeFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', code, 'utf8');
console.log('Successfully wrapped blocks in grid!');
