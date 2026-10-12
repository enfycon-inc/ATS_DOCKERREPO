// Renders illustrative previews from the actual backend templates. No email is sent.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
require(path.join(root, 'ats_backend/node_modules/ts-node')).register({ project: path.join(root, 'ats_backend/tsconfig.json'), transpileOnly: true });
process.env.FRONTEND_URL = 'https://enfyjobs.com';
process.env.BASE_DOMAIN = 'enfyjobs.com';
const { renderSystemEmail, applySystemEmailReplyPolicy } = require(path.join(root, 'ats_backend/src/email/system-email-template.ts'));
const common = { workspace: 'Deb Technology', recipient: 'sahadeb@example.com', fullName: 'Sahadeb' };
const variants = [
  { ...common, event: 'registration_received' },
  { ...common, event: 'workspace_activated', loginUrl: 'https://deb.enfyjobs.com/auth/login' },
  { ...common, event: 'team_invitation', role: 'Recruiter', setupUrl: 'https://enfyjobs.com/auth/setup-password?token=illustrative-preview-only' },
  { ...common, event: 'account_created', role: 'Recruiter', loginUrl: 'https://deb.enfyjobs.com/auth/login' },
  { ...common, event: 'delivery_test' },
];
const frames = [];
for (const variant of variants) {
  const mail = applySystemEmailReplyPolicy({ tenantId: 'preview-only', to: common.recipient, ...renderSystemEmail(variant) }, 'no-reply@enfyjobs.com');
  fs.writeFileSync(path.join(__dirname, variant.event + '.html'), mail.html);
  fs.writeFileSync(path.join(__dirname, variant.event + '.txt'), mail.text);
  frames.push(`<section><h2>${variant.event.replaceAll('_', ' ')}</h2><p>${mail.subject}</p><iframe title="${variant.event}" src="${variant.event}.html"></iframe></section>`);
}
fs.writeFileSync(path.join(__dirname, 'index.html'), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EnfySync system email previews</title><style>body{margin:24px;font:14px Arial;color:#0f172a;background:#e9eef5}h1{color:#1e4e98;font-size:26px}h2{text-transform:capitalize;font-size:18px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}iframe{border:1px solid #cbd5e1;width:100%;height:850px;background:white}p{line-height:1.5}</style></head><body><h1>EnfySync — Corporate system email previews</h1><p>Five actual templates · Illustrative data · No emails sent. Links are preview examples.</p><main>${frames.join('')}</main></body></html>`);
console.log('Generated five HTML and plain-text email previews.');
