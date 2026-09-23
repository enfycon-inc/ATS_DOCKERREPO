const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/components/company/tabs/hiring-tab.tsx', 'utf8');

// 1. Inject the preview function right before the return statement inside HiringTab
const generatePreviewCode = `
  const generatePreview = (pattern: string) => {
    if (!pattern) return "";
    let preview = pattern;
    preview = preview.replace(/{BRANCH}/g, "BLR");
    preview = preview.replace(/{UNIT}/g, "IT");
    
    const d = new Date();
    const yy = String(d.getFullYear()).slice(2);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    
    preview = preview.replace(/{YYMMDD}/g, \`\${yy}\${mm}\${dd}\`);
    preview = preview.replace(/{YYMM}/g, \`\${yy}\${mm}\`);
    preview = preview.replace(/{YY}/g, yy);
    preview = preview.replace(/{MM}/g, mm);
    preview = preview.replace(/{DD}/g, dd);
    
    preview = preview.replace(/{SEQ(?:[:](\\d+))?}/g, (match, p1) => {
      const len = p1 ? parseInt(p1, 10) : 1;
      return "1".padStart(len, "0");
    });
    
    return preview;
  };

`;

const returnIdx = code.indexOf('return (');
if (!code.includes('const generatePreview')) {
    code = code.substring(0, returnIdx) + generatePreviewCode + code.substring(returnIdx);
}

// 2. Replace the token span block to include the live preview
const spanSearch = `<span className="text-[10px] text-neutral-500 block">
                Tokens: <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{BRANCH}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{UNIT}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YYMMDD}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YYMM}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YY}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{MM}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{DD}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{SEQ:4}"}</code>
              </span>`;

const newBlock = `<div className="flex flex-col gap-2 mt-2">
                <span className="text-[10px] text-neutral-500 block">
                  Tokens: <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{BRANCH}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{UNIT}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YYMMDD}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YYMM}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{YY}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{MM}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{DD}"}</code>, <code className="bg-neutral-100 dark:bg-slate-800 px-1 rounded">{"{SEQ:4}"}</code>
                </span>
                
                <div className="bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded p-2 text-xs flex items-center gap-2">
                  <span className="font-semibold text-indigo-700 dark:text-indigo-400">Live Preview:</span>
                  <span className="font-mono font-bold text-indigo-900 dark:text-indigo-300">{generatePreview(jobCodePattern)}</span>
                </div>
              </div>`;

if (code.includes(spanSearch)) {
    code = code.replace(spanSearch, newBlock);
} else {
    // try removing whitespace variations
    const searchRegex = /<span className="text-\[10px\] text-neutral-500 block">[\s\S]*?\{"\{SEQ:4\}"\}<\/code>\s*<\/span>/;
    if (searchRegex.test(code)) {
        code = code.replace(searchRegex, newBlock);
    } else {
        console.log('Could not find span block');
    }
}

fs.writeFileSync('ats_frontend_main/components/company/tabs/hiring-tab.tsx', code, 'utf8');
console.log('Successfully injected live preview!');
