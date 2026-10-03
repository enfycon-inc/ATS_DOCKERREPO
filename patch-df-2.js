const fs = require('fs');
const file = 'scripts/zero_downtime_deploy.sh';
let c = fs.readFileSync(file, 'utf8');

if (!c.includes('BEFORE Cleanup')) {
  c = c.replace(/docker builder prune -af/g, `echo "?? VPS Disk Space BEFORE Cleanup:"\ndf -h /\n\ndocker builder prune -af`);
  fs.writeFileSync(file, c);
}
