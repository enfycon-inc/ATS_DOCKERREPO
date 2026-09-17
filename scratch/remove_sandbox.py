import re

with open('c:/Users/deb/enfyProjects/ATS_DOCKERREPO/ats_frontend_main/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = content.replace('import React, { useState, useTransition } from "react";', 'import React from "react";')
content = content.replace('import { atsApi } from "@/lib/ats-api";\n', '')
content = content.replace('import { signIn } from "next-auth/react";\n', '')
content = content.replace('import toast from "react-hot-toast";\n', '')
content = content.replace('import { getCurrentSubdomain, getBaseDomain, getTenantIdentifier } from "@/utils/subdomain-helper";\n', '')
content = content.replace('import { Loader2, ShieldCheck, User, Users, Briefcase, Settings } from "lucide-react";\n', '')

# 2. Personas array
content = re.sub(r'const personas = \[\s*\{[\s\S]*?\];\n', '', content)

# 3. Inside RootPage
# Remove state
content = re.sub(r'  const \[activeTab, setActiveTab\] = useState<"sandbox" \| "login">\("sandbox"\);\n', '', content)
content = re.sub(r'  const \[isLoggingIn, startLoginTransition\] = useTransition\(\);\n', '', content)
content = re.sub(r'  const \[loginEmail, setLoginEmail\] = useState<string \| null>\(null\);\n', '', content)

# Remove navigateAfterLogin
content = re.sub(r'  /\*\*[\s\S]*?navigateAfterLogin = async \(destination: string\) => \{[\s\S]*?  \};\n', '', content)

# Remove handleQuickLogin
content = re.sub(r'  const handleQuickLogin = async \(email: string, roleName: string\) => \{[\s\S]*?  \};\n', '', content)

# 4. JSX
# Remove tab selector
content = re.sub(r'                \{\/\* Tab selector \*\/\}[\s\S]*?                <\/div>\n\n', '', content)

# Replace activeTab conditional
sandbox_jsx_pattern = r'                \{activeTab === "sandbox" \? \([\s\S]*?                \) : \(\n                  <React\.Suspense fallback=\{<div className="text-center py-6 text-xs text-slate-400">Loading form...<\/div>\}>\n                    <LoginForm \/>\n                  <\/React\.Suspense>\n                \)\}'
replacement = r'                <React.Suspense fallback={<div className="text-center py-6 text-xs text-slate-400">Loading form...</div>}>\n                  <LoginForm />\n                </React.Suspense>'

content = re.sub(sandbox_jsx_pattern, replacement, content)

with open('c:/Users/deb/enfyProjects/ATS_DOCKERREPO/ats_frontend_main/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
