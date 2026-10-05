const fs = require('fs');
const file = 'ats_backend/src/business-units/business-units.service.ts';
let content = fs.readFileSync(file, 'utf8');

let targetCreate = `          ...(dto.branchId ? { branch: { connect: { id: dto.branchId } } } : {}),
          name: dto.name.trim(),
          code,

          ...((dto as any).marketSegmentId ? { marketSegment: { connect: { id: (dto as any).marketSegmentId } } } : {}),`;

let replacementCreate = `          ...(dto.branchId ? { branchId: dto.branchId } : {}),
          name: dto.name.trim(),
          code,

          ...((dto as any).marketSegmentId ? { marketSegmentId: (dto as any).marketSegmentId } : {}),`;

content = content.replace(targetCreate, replacementCreate);

let targetUpdate = `          ...(dto.branchId !== undefined ? (dto.branchId ? { branch: { connect: { id: dto.branchId } } } : { branch: { disconnect: true } }) : {}),
          ...((dto as any).marketSegmentId !== undefined ? ((dto as any).marketSegmentId ? { marketSegment: { connect: { id: (dto as any).marketSegmentId } } } : { marketSegment: { disconnect: true } }) : {}),`;

let replacementUpdate = `          ...(dto.branchId !== undefined ? { branchId: dto.branchId || null } : {}),
          ...((dto as any).marketSegmentId !== undefined ? { marketSegmentId: (dto as any).marketSegmentId || null } : {}),`;

content = content.replace(targetUpdate, replacementUpdate);

fs.writeFileSync(file, content);
