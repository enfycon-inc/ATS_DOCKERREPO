const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', 'utf8');

code = code.replace(
  '</div>\n  \n              {/* Modal Footer */}',
  '</div>\n              </div>\n  \n              {/* Modal Footer */}'
);

fs.writeFileSync('ats_frontend_main/app/(dashboard)/utility/users/page.tsx', code);
