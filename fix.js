const fs = require('fs');
let c = fs.readFileSync('ats_frontend_main/app/(dashboard)/job-posting/[id]/page.tsx', 'utf8');

c = c.replace(/\{canSubmitCandidate && \(\r?\n<Button[\s\S]*?<\/Button>\r?\n\)\}/g, (match) => {
    // Just remove the newlines around the wrapper to see if it fixes it
    return '{canSubmitCandidate && (' + match.substring(24, match.length - 2) + ')}';
});

fs.writeFileSync('ats_frontend_main/app/(dashboard)/job-posting/[id]/page.tsx', c);
