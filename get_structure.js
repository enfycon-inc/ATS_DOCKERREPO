const fs = require('fs');
const code = fs.readFileSync('ats_frontend_main/components/company/tabs/hiring-tab.tsx', 'utf8');
const lines = code.split('\n');
const structure = [];
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('<div className="grid') || lines[i].includes('</Card>') || lines[i].includes('<Card ') || lines[i].includes('<div className="space-y-6"') || lines[i].includes('return (')) {
    structure.push(i+1 + ": " + lines[i].trim());
  }
}
console.log(structure.join('\n'));
