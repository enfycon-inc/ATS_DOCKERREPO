with open('ats_frontend_main/components/company/auth-policy-card.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

import re

pattern = re.compile(r'return \(\s*<Card className=.*$', re.DOTALL)

new_render = '''return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative">
      {/* Left Column (7 cols): Divided into distinct Cards for clarity */}
      <div className="lg:col-span-7 space-y-6">
        
        {/* Card 1: Basic Authentication Methods */}
        <Card className="border border-neutral-200 shadow-sm dark:border-slate-800 dark:bg-slate-900/40">
          <CardHeader className="pb-3 border-b border-neutral-150 dark:border-slate-800/60 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold flex items-center gap-1.5 text-neutral-800 dark:text-neutral-100">
                <KeyRound className="h-4 w-4 text-emerald-600 dark:text-emerald-500" />
                Allowed Sign-In Methods for Workspace Members
              </CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadPolicy}
              disabled={loading}
              className="h-8 text-xs font-semibold px-2.5 flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </CardHeader>
          <CardContent className="pt-5 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Password */}
              <div className={`p-3 rounded-lg border transition-all ${allowPasswordLogin ? "border-emerald-300 bg-emerald-50/20 dark:border-emerald-800/60 dark:bg-emerald-950/10" : "border-neutral-200 dark:border-slate-800 bg-neutral-50/50 dark:bg-slate-900/50 opacity-75"}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-neutral-600 dark:text-neutral-400" />
                    <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Password</span>
                  </div>
                  <Switch checked={allowPasswordLogin} onCheckedChange={handleTogglePassword} disabled={loading} />
                </div>
                <p className="text-[11px] text-neutral-500 leading-snug">Sign in with email and encrypted password.</p>
              </div>

              {/* Microsoft SSO */}
              <div className={`p-3 rounded-lg border transition-all ${allowMicrosoftSso ? "border-emerald-300 bg-emerald-50/20 dark:border-emerald-800/60 dark:bg-emerald-950/10" : "border-neutral-200 dark:border-slate-800 bg-neutral-50/50 dark:bg-slate-900/50 opacity-75"}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <svg width="12" height="12" viewBox="0 0 21 21">
                      <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                      <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                      <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                      <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                    </svg>
                    <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Microsoft</span>
                  </div>
                  <Switch checked={allowMicrosoftSso} onCheckedChange={handleToggleMicrosoft} disabled={loading} />
                </div>
                <p className="text-[11px] text-neutral-500 leading-snug">Sign-in via Microsoft Entra ID (Office 365).</p>
              </div>

              {/* Google SSO */}
              <div className={`p-3 rounded-lg border transition-all ${allowGoogleSso ? "border-emerald-300 bg-emerald-50/20 dark:border-emerald-800/60 dark:bg-emerald-950/10" : "border-neutral-200 dark:border-slate-800 bg-neutral-50/50 dark:bg-slate-900/50 opacity-75"}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 24 24">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
                    </svg>
                    <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Google</span>
                  </div>
                  <Switch checked={allowGoogleSso} onCheckedChange={handleToggleGoogle} disabled={loading} />
                </div>
                <p className="text-[11px] text-neutral-500 leading-snug">Sign-in via Google Workspace accounts.</p>
              </div>
            </div>

            {/* Enforce SSO */}
            <div className="flex items-center justify-between p-3.5 rounded-lg border border-neutral-200 dark:border-slate-800 bg-white dark:bg-slate-900/60">
              <div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <Label className="text-xs font-bold text-neutral-800 dark:text-neutral-200 cursor-pointer" htmlFor="enforce-sso-switch">
                    Enforce SSO Only (Disable Password Login)
                  </Label>
                  <Badge variant="outline" className="text-[9px] h-4 px-1 ml-1 bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900">ENTERPRISE</Badge>
                </div>
                <p className="text-[11px] text-neutral-500 mt-1">
                  When enabled, password-based login is completely disabled for this workspace. All users must authenticate via Google or Microsoft SSO.
                </p>
              </div>
              <Switch
                id="enforce-sso-switch"
                checked={enforceSsoOnly}
                onCheckedChange={handleToggleEnforceSso}
                disabled={loading || (!allowMicrosoftSso && !allowGoogleSso)}
              />
            </div>

            <div className="flex justify-end pt-2">
                <Button type="button" onClick={handleSave} disabled={saving || loading} size="sm" className="text-xs font-bold px-4 cursor-pointer bg-primary hover:bg-primary/90">
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  {saving ? "Saving..." : "Save Authentication Methods"}
                </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Corporate Email Whitelist */}
        <Card className="border border-neutral-200 shadow-sm dark:border-slate-800 dark:bg-slate-900/40">
          <CardContent className="pt-5 space-y-4">
            <div>
              <div className="flex justify-between items-center mb-1">
                <div className="flex items-center gap-1.5">
                  <Building className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  <Label className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                    Allowed Email Domains (Corporate Whitelist)
                  </Label>
                </div>
                <span className="text-[10px] text-neutral-400 dark:text-neutral-500">
                  {allowedEmailDomains.length === 0 ? "Any domain allowed" : `${allowedEmailDomains.length} domains restricted`}
                </span>
              </div>
              <p className="text-[11px] text-neutral-500 mb-2.5">
                Specify corporate email domains permitted to access this workspace (e.g. deb.com). Logins from outside domains (e.g. enfycon.com) will be blocked.
              </p>
              
              <div className="flex items-center gap-2 mb-3">
                <Input
                  type="text"
                  placeholder="@ e.g. deb.com or company.com"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value.toLowerCase().replace(/\s/g, ''))}
                  onKeyDown={handleAddDomainKeyDown}
                  className="h-9 text-xs font-mono bg-white dark:bg-slate-900"
                />
                <Button 
                  type="button"
                  onClick={handleAddDomain}
                  variant="outline" 
                  className="h-9 px-3 text-xs font-semibold shrink-0 cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Domain
                </Button>
              </div>

              {allowedEmailDomains.length > 0 ? (
                <div className="flex flex-wrap gap-2 p-3 bg-neutral-50 dark:bg-slate-900/50 rounded-lg border border-neutral-150 dark:border-slate-800/80">
                  {allowedEmailDomains.map((domain) => (
                    <Badge key={domain} variant="secondary" className="text-[11px] font-mono py-1 px-2.5 bg-white dark:bg-slate-800 border border-neutral-200 dark:border-slate-700 flex items-center gap-1.5">
                      @{domain}
                      <button onClick={() => handleRemoveDomain(domain)} className="text-neutral-400 hover:text-red-500 cursor-pointer focus:outline-none">
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              ) : (
                <div className="text-[10px] text-neutral-400 italic">
                  No domain restrictions configured. Any invited user can sign in.
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
                <Button type="button" onClick={handleSave} disabled={saving || loading} size="sm" className="text-xs font-bold px-4 cursor-pointer bg-primary hover:bg-primary/90">
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  {saving ? "Saving..." : "Save Email Whitelist"}
                </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Security Constraints */}
        <Card className="border border-neutral-200 shadow-sm dark:border-slate-800 dark:bg-slate-900/40">
          <CardContent className="pt-5 space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <Lock className="h-4 w-4 text-blue-600 dark:text-blue-500" />
                <Label className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                  Microsoft Azure AD Directory (Tenant) ID Lock
                </Label>
                <Badge variant="outline" className="text-[9px] h-4 px-1 ml-1 bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-950/30 dark:border-blue-900">TENANT ISOLATION</Badge>
              </div>
              <p className="text-[11px] text-neutral-500 mb-2.5">
                Enter your Microsoft 365 Azure Tenant ID GUID to restrict Microsoft SSO exclusively to your company's directory. Outside Microsoft organizations will be blocked.
              </p>
              <Input
                type="text"
                placeholder="e.g. 9188040d-6c67-4c5b-b112-36a304b66dad"
                value={microsoftTenantId}
                onChange={(e) => setMicrosoftTenantId(e.target.value.trim())}
                className="h-9 text-xs font-mono mb-1.5"
              />
              <p className="text-[10px] text-neutral-400 flex items-center gap-1">
                <HelpCircle className="h-3 w-3" />
                Found in Azure Portal &gt; Microsoft Entra ID &gt; Overview &gt; Tenant ID.
              </p>
            </div>

            <div className="flex justify-end pt-2">
                <Button type="button" onClick={handleSave} disabled={saving || loading} size="sm" className="text-xs font-bold px-4 cursor-pointer bg-primary hover:bg-primary/90">
                  <Save className="h-3.5 w-3.5 mr-1.5" />
                  {saving ? "Saving..." : "Save Tenant ID Lock"}
                </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card 4: Bring Your Own App (Custom SSO) */}
        <Card className="border border-emerald-200 shadow-sm dark:border-emerald-900/40 bg-emerald-50/10 dark:bg-emerald-950/5">
          <CardContent className="pt-5 space-y-4">
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-500" />
                <Label className="text-xs font-bold text-emerald-800 dark:text-emerald-300">
                  Bring Your Own App (Custom SSO Integration)
                </Label>
                <Badge variant="outline" className="text-[9px] h-4 px-1 ml-1 bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900">ENTERPRISE</Badge>
              </div>
              <p className="text-[11px] text-neutral-500 mb-3">
                If you have created a Single-Tenant App Registration in your own Azure Portal, provide your Client ID and Secret below to automatically generate your SSO Redirect URIs.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <Label className="text-[10px] font-semibold text-neutral-600 uppercase tracking-wider mb-1 block">Client ID</Label>
                  <Input
                    type="text"
                    placeholder="e.g. a753542d-..."
                    value={microsoftClientId}
                    onChange={(e) => setMicrosoftClientId(e.target.value.trim())}
                    className="h-9 text-xs font-mono bg-white dark:bg-slate-900"
                  />
                </div>
                <div>
                  <Label className="text-[10px] font-semibold text-neutral-600 uppercase tracking-wider mb-1 block">Client Secret</Label>
                  <Input
                    type="password"
                    placeholder="Enter Client Secret"
                    value={microsoftClientSecret}
                    onChange={(e) => setMicrosoftClientSecret(e.target.value.trim())}
                    className="h-9 text-xs font-mono bg-white dark:bg-slate-900"
                  />
                </div>
              </div>
              
              {microsoftRedirectUri && (
                  <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg dark:bg-blue-950/20 dark:border-blue-900/40 space-y-2 mt-4">
                      <div>
                        <Label className="text-[10px] font-semibold text-blue-800 dark:text-blue-300 uppercase tracking-wider mb-1 block">Production Redirect URI</Label>
                        <p className="text-[11px] text-blue-700 dark:text-blue-400 mb-1">Paste this exact URL into the "Redirect URIs" section of your Azure App Registration.</p>
                        <code className="block p-2 bg-white dark:bg-slate-900 rounded border border-blue-200 dark:border-blue-800 text-[10px] font-mono text-neutral-800 dark:text-neutral-300 break-all select-all">
                            {microsoftRedirectUri}
                        </code>
                      </div>
                      
                      {typeof window !== 'undefined' && window.location.hostname.includes('localhost') && (
                        <div className="pt-2 border-t border-blue-200 dark:border-blue-800/50">
                          <Label className="text-[10px] font-semibold text-blue-800 dark:text-blue-300 uppercase tracking-wider mb-1 block">Localhost Testing Redirect URI</Label>
                          <p className="text-[10px] text-blue-700 dark:text-blue-400 mb-1">Since you are on localhost, also add this URI to test SSO locally.</p>
                          <code className="block p-2 bg-white dark:bg-slate-900 rounded border border-blue-200 dark:border-blue-800 text-[10px] font-mono text-neutral-800 dark:text-neutral-300 break-all select-all">
                              {microsoftRedirectUri.replace('https://auth.enfyjobs.com', 'http://localhost:8080')}
                          </code>
                        </div>
                      )}
                  </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
                <Button type="button" onClick={handleSave} disabled={saving || loading} size="sm" className="text-xs font-bold px-4 cursor-pointer bg-emerald-600 hover:bg-emerald-700 text-white">
                  <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${saving ? "animate-spin" : ""}`} />
                  {saving ? "Generating..." : "Save App & Generate URLs"}
                </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right Column (5 cols): Live Interactive Employee Login Preview (Side by Side) */}
      <div className="lg:col-span-5 lg:sticky lg:top-4 space-y-2 h-fit">
        <div className="p-4 rounded-xl border border-neutral-250 dark:border-slate-800 bg-neutral-50/60 dark:bg-slate-900/50 space-y-3.5 shadow-xs">
          <div className="flex items-center justify-between pb-1.5 border-b border-neutral-200/60 dark:border-slate-800">
            <div className="flex items-center gap-1.5">
              <Eye className="h-3.5 w-3.5 text-primary" />
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Live Employee Preview
              </span>
            </div>
            <span className="text-[10px] font-mono text-primary font-semibold truncate max-w-[180px]" title={subdomain ? `${subdomain}.enfyjobs.com/auth/login` : "enfyjobs.com/auth/login"}>
              {subdomain ? `${subdomain}.enfyjobs.com` : "enfyjobs.com"}
            </span>
          </div>

          {/* Login Card Preview */}
          <div className="w-full max-w-sm mx-auto p-4 bg-white dark:bg-slate-900 rounded-xl border border-neutral-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="text-center pb-1">
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">{companyName || "Your Workspace"}</h4>
              <p className="text-[10px] text-slate-400">Sign in to your account</p>
            </div>

            {/* Simulated Password Fields */}
            {allowPasswordLogin ? (
              <div className="space-y-2">
                <div className="space-y-1">
                  <div className="h-2 w-14 bg-slate-200 dark:bg-slate-700 rounded" />
                  <div className="h-7 w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded flex items-center px-2 text-[10px] text-slate-400 font-mono">
                    user@{allowedEmailDomains[0] || "company.com"}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="h-2 w-12 bg-slate-200 dark:bg-slate-700 rounded" />
                  <div className="h-7 w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded flex items-center px-2 text-[10px] text-slate-400">
                    ••••••••••••
                  </div>
                </div>
                <div className="h-7 w-full bg-indigo-600 rounded flex items-center justify-center text-[10px] font-semibold text-white">
                  Sign In to Workspace
                </div>
              </div>
            ) : (
              <div className="p-3 bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/80 rounded-lg text-center space-y-1">
                <ShieldCheck className="h-4 w-4 text-emerald-600 mx-auto" />
                <p className="text-[11px] font-bold text-slate-800 dark:text-slate-200">Single Sign-On Enforced</p>
                <p className="text-[10px] text-slate-500 leading-snug">Password login is disabled. Sign in via your corporate identity provider below.</p>
              </div>
            )}

            {/* Simulated Social SSO buttons */}
            {(allowMicrosoftSso || allowGoogleSso) && (
              <div className="space-y-2 pt-1">
                {allowPasswordLogin && (
                  <div className="relative flex items-center justify-center my-1.5">
                    <div className="border-t border-slate-200 dark:border-slate-800 w-full" />
                    <span className="absolute bg-white dark:bg-slate-900 px-2 text-[9px] uppercase font-semibold text-slate-400">
                      Or Sign In With
                    </span>
                  </div>
                )}
                <div className={`grid gap-2 ${allowMicrosoftSso && allowGoogleSso ? "grid-cols-2" : "grid-cols-1"}`}>
                  {allowGoogleSso && (
                    <div className="h-8 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center gap-1.5 text-[10px] font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800">
                      <svg width="12" height="12" viewBox="0 0 24 24">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
                      </svg>
                      Google
                    </div>
                  )}
                  {allowMicrosoftSso && (
                    <div className="h-8 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center gap-1.5 text-[10px] font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800">
                      <svg width="12" height="12" viewBox="0 0 21 21">
                        <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                        <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                        <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                        <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                      </svg>
                      Microsoft
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <p className="text-[10px] text-neutral-400 dark:text-neutral-500 text-center">
            Updates dynamically as you change sign-in methods on the left.
          </p>
        </div>
      </div>
    </div>
  );
}
'''
new_content = pattern.sub(new_render, content)

with open('ats_frontend_main/components/company/auth-policy-card.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
