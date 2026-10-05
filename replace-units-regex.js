const fs = require('fs');
const file = 'ats_backend/src/business-units/business-units.service.ts';
let content = fs.readFileSync(file, 'utf8');

const regexCreate = /\.\.\.\(dto\.branchId \? \{ branch: \{ connect: \{ id: dto\.branchId \} \} \} : \{\}\),\s*name: dto\.name\.trim\(\),\s*code,\s*\.\.\.\(\(dto as any\)\.marketSegmentId \? \{ marketSegment: \{ connect: \{ id: \(dto as any\)\.marketSegmentId \} \} \} : \{\}\),/m;
const replacementCreate = `...(dto.branchId ? { branchId: dto.branchId } : {}),\n          name: dto.name.trim(),\n          code,\n\n          ...((dto as any).marketSegmentId ? { marketSegmentId: (dto as any).marketSegmentId } : {}),`;

content = content.replace(regexCreate, replacementCreate);

const regexUpdate = /\.\.\.\(dto\.branchId !== undefined \? \(dto\.branchId \? \{ branch: \{ connect: \{ id: dto\.branchId \} \} \} : \{ branch: \{ disconnect: true \} \}\) : \{\}\),\s*\.\.\.\(\(dto as any\)\.marketSegmentId !== undefined \? \(\(dto as any\)\.marketSegmentId \? \{ marketSegment: \{ connect: \{ id: \(dto as any\)\.marketSegmentId \} \} \} : \{ marketSegment: \{ disconnect: true \} \}\) : \{\}\),/m;
const replacementUpdate = `...(dto.branchId !== undefined ? { branchId: dto.branchId || null } : {}),\n          ...((dto as any).marketSegmentId !== undefined ? { marketSegmentId: (dto as any).marketSegmentId || null } : {}),`;

content = content.replace(regexUpdate, replacementUpdate);

fs.writeFileSync(file, content);
