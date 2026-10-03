const fs = require('fs');
const file = 'scripts/zero_downtime_deploy.sh';
let c = fs.readFileSync(file, 'utf8');

c = c.replace(/echo "?? Cleaning up old Docker build cache and unused images to free up VPS disk space..."/g, `echo "?? VPS Disk Space BEFORE Cleanup:"\ndf -h /\n\necho "?? Cleaning up old Docker build cache and unused images to free up VPS disk space..."`);

c = c.replace(/docker image prune -af \|\| true/g, `docker image prune -af || true\n\necho "?? VPS Disk Space AFTER Cleanup:"\ndf -h /`);

fs.writeFileSync(file, c);
