file_path = r"ats_backend\src\auth\services\auth-init.service.ts"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

import re
unit_admin_match = re.search(r"\('Unit Admin', 'UNIT_ADMIN', '(\[.*?\])'\)", code)
if unit_admin_match:
    new_perms = unit_admin_match.group(1)
    code = re.sub(r"\('Delivery Head', 'DELIVERY_HEAD', '\[.*?\]'\)", f"('Delivery Head', 'DELIVERY_HEAD', '{new_perms}')", code)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Updated auth-init.service.ts locally")
else:
    print("Could not find Unit Admin")
