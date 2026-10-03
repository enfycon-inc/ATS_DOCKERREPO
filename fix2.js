const fs = require('fs');
let c = fs.readFileSync('ats_frontend_main/app/(dashboard)/job-posting/[id]/page.tsx', 'utf8');

c = c.replace(/\{canSubmitCandidate && \(\r?\n<Button([\s\S]*?)<\/Button>\r?\n\)\}/g, '{canSubmitCandidate && <Button</Button>}');

fs.writeFileSync('ats_frontend_main/app/(dashboard)/job-posting/[id]/page.tsx', c);
