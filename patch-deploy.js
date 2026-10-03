const fs = require('fs');
const file = '.github/workflows/deploy.yml';
let c = fs.readFileSync(file, 'utf8');

const injection = `
      - name: Free Disk Space (Ubuntu)
        uses: jlumbroso/free-disk-space@main
        with:
          tool-cache: true
          android: true
          dotnet: true
          haskell: true
          large-packages: true
          docker-images: false
          swap-storage: false

      - name: Checkout Frontend
`;
c = c.replace(/      - name: Checkout Frontend/g, injection.trim() + '\n        uses: actions/checkout');

fs.writeFileSync(file, c);
