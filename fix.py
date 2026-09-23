
import sys

path = r"c:\Users\deb\enfyProjects\ATS_DOCKERREPO\ats_frontend_main\app\(dashboard)\utility\roles-permissions\page.tsx"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    "if(confirm(Are you sure you want to delete  roles?)) {",
    "if(confirm(`Are you sure you want to delete ${selectedRoleIds.length} roles?`)) {"
)
code = code.replace(
    "toast.success(Deleted  roles successfully!);",
    "toast.success(`Deleted ${selectedRoleIds.length} roles successfully!`);"
)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed properly!")

