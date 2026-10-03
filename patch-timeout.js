const fs = require('fs');
const file = '.github/workflows/deploy.yml';
let c = fs.readFileSync(file, 'utf8');

c = c.replace(/command_timeout: 10m/g, 'command_timeout: 30m');

fs.writeFileSync(file, c);
