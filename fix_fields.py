
import sys

path = r"c:\Users\deb\enfyProjects\ATS_DOCKERREPO\ats_frontend_main\app\(dashboard)\utility\roles-permissions\page.tsx"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    "const res = await fetch(https://api.zippopotam.us/us/);",
    "const res = await fetch(`https://api.zippopotam.us/us/${quickAddUnitZip}`);"
)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("Fixed backticks!")

