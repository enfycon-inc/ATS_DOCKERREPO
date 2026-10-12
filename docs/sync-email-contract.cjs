const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'ats_backend/src/email/system-email.types.ts'), 'utf8');
const target = path.join(root, 'ats_frontend_main/lib/system-email.types.ts');
const generated = '// Generated from ats_backend/src/email/system-email.types.ts. Run docs/sync-email-contract.cjs to update.\n' + source;
if (process.argv.includes('--check')) {
  if (fs.readFileSync(target, 'utf8').replace(/\r\n/g, '\n') !== generated.replace(/\r\n/g, '\n')) {
    throw new Error('Email API contract changed. Run node docs/sync-email-contract.cjs before building.');
  }
  console.log('Email API contract is synchronized.');
} else {
  fs.writeFileSync(target, generated);
  console.log('Frontend email API contract updated.');
}
