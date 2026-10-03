const fs = require('fs');
const file = 'scripts/zero_downtime_deploy.sh';
let c = fs.readFileSync(file, 'utf8');

const cleanup = `
echo "?? Cleaning up old Docker build cache and unused images to free up VPS disk space..."
docker builder prune -af || true
docker image prune -af || true

# Pull core images
`;
c = c.replace(/# Pull core images\s*\n/g, cleanup);

fs.writeFileSync(file, c);
