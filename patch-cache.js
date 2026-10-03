const fs = require('fs');
const file = '.github/workflows/deploy.yml';
let c = fs.readFileSync(file, 'utf8');

c = c.replace(/cache-from: type=gha\s+cache-to: type=gha,mode=max/g, (match, offset, string) => {
    // figure out which one we are replacing based on context
    let scope = 'default';
    let preceding = string.substring(0, offset);
    if (preceding.includes('ats-backend:latest')) { scope = 'ats-backend'; }
    if (preceding.includes('ats-frontend:latest')) { scope = 'ats-frontend'; }
    if (preceding.includes('ats-parser:latest')) { scope = 'ats-parser'; }
    return `cache-from: type=gha,scope=${scope}\n          cache-to: type=gha,mode=max,scope=${scope}`;
});

fs.writeFileSync(file, c);
