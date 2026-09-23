const fs = require('fs');
let code = fs.readFileSync('ats_backend/prisma/schema.prisma', 'utf8');

const insertIdx = code.indexOf('name                      String                 @db.VarChar(255)') + 65;

const newFields = '\n    logoUrl                   String?                @map("logo_url") @db.VarChar(2048)\n    siteTitle                 String?                @map("site_title") @db.VarChar(255)';

code = code.substring(0, insertIdx) + newFields + code.substring(insertIdx);

fs.writeFileSync('ats_backend/prisma/schema.prisma', code, 'utf8');
console.log('Successfully patched schema.prisma');
