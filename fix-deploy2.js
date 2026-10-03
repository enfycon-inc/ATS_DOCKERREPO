const fs = require('fs');
const file = '.github/workflows/deploy.yml';
let c = fs.readFileSync(file, 'utf8');

// Revert the job-level if condition
c = c.replace(
  "if: github.ref == 'refs/heads/main' && (github.event_name != 'repository_dispatch' || github.event.client_payload.repo == matrix.repo)",
  "if: github.ref == 'refs/heads/main'"
);

// We need to inject the skip condition on all steps in the build job.
// Find the "steps:" section inside "build:"
const stepsIndex = c.indexOf('    steps:\n');

const checkStep = `    steps:
      - name: Check if matrix job should run
        id: check
        run: |
          if [ "\${{ github.event_name }}" == "repository_dispatch" ] && [ "\${{ github.event.client_payload.repo }}" != "\${{ matrix.repo }}" ]; then
            echo "skip=true" >> $GITHUB_ENV
          fi

`;

c = c.replace('    steps:\n', checkStep);

// Now for every step inside build: add the if condition.
// Free disk space step already has an if. We will change it to include our check.
c = c.replace(
  "        if: matrix.tag == 'ats-parser'",
  "        if: matrix.tag == 'ats-parser' && env.skip != 'true'"
);

// For the rest of the steps, they don't have an if condition yet.
c = c.replace(
  "      - name: Checkout Microservice",
  "      - name: Checkout Microservice\n        if: env.skip != 'true'"
);

c = c.replace(
  "      - name: Set up Docker Buildx",
  "      - name: Set up Docker Buildx\n        if: env.skip != 'true'"
);

c = c.replace(
  "      - name: Log in to GitHub Container Registry",
  "      - name: Log in to GitHub Container Registry\n        if: env.skip != 'true'"
);

c = c.replace(
  "      - name: Build and Push Image",
  "      - name: Build and Push Image\n        if: env.skip != 'true'"
);

fs.writeFileSync(file, c);
console.log('Fixed deploy.yml steps');
