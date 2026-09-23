const fs = require('fs');
let code = fs.readFileSync('ats_frontend_main/lib/role-permissions.ts', 'utf8');

const search = `          ],
        };
      }
      return item;
    });
  }`;

const replace = `          ],
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
    });
  }`;

if(code.indexOf(search) !== -1) {
    code = code.replace(search, replace);
    fs.writeFileSync('ats_frontend_main/lib/role-permissions.ts', code, 'utf8');
    console.log('Done!');
} else {
    // maybe windows CRLF
    const s2 = search.replace(/\n/g, '\r\n');
    if (code.indexOf(s2) !== -1) {
        code = code.replace(s2, replace.replace(/\n/g, '\r\n'));
        fs.writeFileSync('ats_frontend_main/lib/role-permissions.ts', code, 'utf8');
        console.log('Done 3!');
    } else {
        console.log('STILL NOT FOUND');
    }
}
