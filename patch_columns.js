const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/components/company/tabs/hiring-tab.tsx', 'utf8');

// The original grid layout:
// <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
//   <Card 1> (Candidate Pool)
//   <Card 2> (Job Code Pattern)  -- has mt-6
//   <div className="space-y-6">
//     <Card 3>
//     <Card 4>
//     <Card 5>
//   </div>
// </div>

// First, wrap Card 1 in a left-column div.
code = code.replace(
  '{/* 1. Candidate Pool Mode Card */}',
  '        {/* LEFT COLUMN */}\n        <div className="space-y-6">\n          {/* 1. Candidate Pool Mode Card */}'
);

// Close the left column div right before Card 2
const card2Comment = '{/* Job Code Pattern Settings Card */}';
code = code.replace(
  card2Comment,
  '        </div>\n\n        {/* RIGHT COLUMN */}\n        <div className="space-y-6">\n          ' + card2Comment
);

// Remove the `mt-6` from Card 2
code = code.replace(
  '<Card className="border border-neutral-200 dark:border-slate-800/80 shadow-xs bg-white dark:bg-slate-900 flex flex-col mt-6">',
  '<Card className="border border-neutral-200 dark:border-slate-800/80 shadow-xs bg-white dark:bg-slate-900 flex flex-col">'
);

// Card 3, 4, 5 were already wrapped in `<div className="space-y-6">` just before Card 3.
// We should remove that `<div className="space-y-6">` (since they are now under the RIGHT COLUMN's space-y-6)
// Wait, Card 3 comment is `{/* 2. Pod System Settings Card */}`
const card3Comment = '{/* 2. Pod System Settings Card */}';
// The code looks like:
//       {/* 2. Pod System Settings Card */}
//         <div className="space-y-6">
//           <Card className="border ...
// Let's replace the `div className="space-y-6"` directly under that comment.
const oldDivStr = '{/* 2. Pod System Settings Card */}\n        <div className="space-y-6">';
if (code.includes(oldDivStr)) {
  code = code.replace(oldDivStr, '{/* 2. Pod System Settings Card */}');
} else {
  // Regex approach
  code = code.replace(/\{\/\* 2\. Pod System Settings Card \*\/}\s*<div className="space-y-6">/, '{/* 2. Pod System Settings Card */}');
}

// Since we opened a `<div className="space-y-6">` for the RIGHT COLUMN, we must ensure it closes exactly where the old `<div className="space-y-6">` was closing!
// Fortunately, the old one was closing at the end of the cards, which is exactly where the new RIGHT COLUMN div should close.
// So the total number of opening/closing divs doesn't change! We just moved the opening div from right before Card 3 to right before Card 2.

fs.writeFileSync('ats_frontend_main/components/company/tabs/hiring-tab.tsx', code, 'utf8');
console.log('Successfully re-arranged columns!');
