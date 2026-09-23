const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/lib/role-permissions.ts', 'utf8');

const search = `            { label: "Job Boards", href: "/job-posting/boards" },
          ],
        };
      }
      return item;
    });`;

const searchCrLf = search.replace(/\n/g, '\r\n');

const replace = `            { label: "Job Boards", href: "/job-posting/boards" },
          ],
        };
      }
      if (item.id === "branch-units") {
        if (!permissions.includes("tenant:settings")) {
          return {
            ...item,
            children: item.children ? item.children.filter((child) => child.href !== "/management/markets") : undefined,
          };
        }
      }
      return item;
    });`;

if(code.includes(search)) {
    code = code.replace(search, replace);
} else if (code.includes(searchCrLf)) {
    code = code.replace(searchCrLf, replace.replace(/\n/g, '\r\n'));
}

fs.writeFileSync('ats_frontend_main/lib/role-permissions.ts', code, 'utf8');
console.log('Done!');
