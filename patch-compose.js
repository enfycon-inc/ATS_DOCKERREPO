const fs = require('fs');
const file = 'docker-compose.prod.yml';
let c = fs.readFileSync(file, 'utf8');

// Replace build context with image for frontend and backend, both blue and green
c = c.replace(/build:\s*\n\s*context: \.\/ats_frontend_main\s*\n\s*dockerfile: Dockerfile\.prod/g, 'image: ghcr.io/enfycon-inc/ats-frontend:latest');
c = c.replace(/build:\s*\n\s*context: \.\/ats_backend\s*\n\s*dockerfile: Dockerfile\.prod/g, 'image: ghcr.io/enfycon-inc/ats-backend:latest');
c = c.replace(/build:\s*\n\s*context: \.\/resume-parser-main\s*\n\s*dockerfile: Dockerfile/g, 'image: ghcr.io/enfycon-inc/ats-parser:latest');

fs.writeFileSync(file, c);
