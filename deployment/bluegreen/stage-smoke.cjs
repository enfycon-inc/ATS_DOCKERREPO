// Runs inside the backend container; credentials stay in environment/memory.
const fs = require('fs');
const crypto = require('crypto');
const base = 'http://127.0.0.1:5000';
async function request(method, path, body, token, extra = {}) {
  const response = await fetch(base + path, {
    method,
    headers: {'Content-Type':'application/json', ...(token ? {Authorization:'Bearer '+token} : {}), ...extra},
    ...(body ? {body:JSON.stringify(body)} : {}),
    signal: AbortSignal.timeout(30000),
  });
  const data = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(`${method} ${path}: ${response.status} ${JSON.stringify(data).slice(0,500)}`);
  return data;
}
async function main() {
  await request('GET','/api/health'); console.log('PASS backend health');
  const platform = await request('POST','/api/auth/login',{email:process.env.PLATFORM_ADMIN_EMAIL,password:process.env.PLATFORM_ADMIN_PASSWORD});
  if (!platform.accessToken || !platform.refreshToken) throw new Error('Platform token pair missing');
  console.log('PASS platform password login');
  const issuer = JSON.parse(Buffer.from(platform.accessToken.split('.')[1], 'base64url').toString()).iss;
  if (!issuer.endsWith('/realms/enfycon-ats')) throw new Error('Unexpected issuer: '+issuer);
  console.log('PASS isolated Keycloak token issuer');
  const renewed = await request('POST','/api/auth/refresh',{refreshToken:platform.refreshToken});
  if (!renewed.accessToken) throw new Error('Renewal token missing');
  console.log('PASS session renewal');
  const suffix = Date.now().toString(36);
  const password = crypto.randomBytes(20).toString('hex');
  const slug = 'deployment-check-'+suffix;
  const email = 'deployment-check-'+suffix+'@example.invalid';
  const registered = await request('POST','/api/auth/register-tenant',{companyName:'Deployment Verification '+suffix,subdomain:slug,email,fullName:'Deployment Verification',password});
  const tenantId=registered.tenant.id, userId=registered.user.id;
  fs.writeFileSync('/tmp/ats-smoke-identifiers.json',JSON.stringify({tenantId,userId,slug,email}));
  console.log('PASS tenant/account registration');
  await request('POST','/api/auth/approvals/approve/'+userId,{market:'IN',subdomain:slug,userLimit:5,maxBranches:3},platform.accessToken);
  console.log('PASS account approval');
  const login = await request('POST','/api/auth/login',{email,password,subdomain:slug});
  if (!login.accessToken || !login.refreshToken) throw new Error('Tenant token pair missing');
  console.log('PASS tenant password login');
  const profile = await request('GET','/api/auth/me',null,login.accessToken);
  if (profile.tenantId !== tenantId) throw new Error('Profile tenant mismatch');
  console.log('PASS tenant profile and permissions');
  const headers={'x-tenant-id':tenantId};
  const branch=await request('POST','/api/branches',{name:'Verification Office',code:'VERIFY',city:'Bhubaneswar',country:'India',timezone:'Asia/Kolkata',workStartTime:'09:00',workEndTime:'18:00',market:'IN'},login.accessToken,headers);
  console.log('PASS branch creation');
  const unit=await request('POST','/api/business-units',{name:'Verification Unit',code:'VERIFY-UNIT',branchId:branch.id,market:'IN',currency:'INR',timezone:'Asia/Kolkata',workStartTime:'09:00',workEndTime:'18:00'},login.accessToken,headers);
  console.log('PASS unit creation');
  await request('PUT','/api/business-units/'+unit.id,{workStartTime:'10:15',workEndTime:'19:15'},login.accessToken,headers);
  const saved=await request('GET','/api/business-units/'+unit.id,null,login.accessToken,headers);
  if(saved.workStartTime!=='10:15'||saved.workEndTime!=='19:15')throw new Error('Unit schedule did not persist');
  console.log('PASS unit schedule save/reload');
  const job=await request('POST','/api/jobs',{title:'Deployment Verification Java Developer',client:'Verification Client',type:'Full-time',description:'Verification of production job creation.',skillsRequired:['Java'],branchId:branch.id,businessUnitId:unit.id,market:'IN',workMode:'In Office',noOfPositions:1},login.accessToken,{...headers,'x-branch-id':branch.id});
  if(!job.id)throw new Error('Created job identifier missing');
  console.log('PASS job creation');
  const fetched=await request('GET','/api/jobs/'+job.id,null,login.accessToken,headers);
  if(fetched.businessUnitId!==unit.id)throw new Error('Job operating unit did not persist');
  console.log('PASS job reload and operating unit persistence');
  const forbidden=await fetch(base+'/api/branches',{headers:{Authorization:'Bearer '+login.accessToken,'x-tenant-id':process.env.DEFAULT_TENANT_ID}});
  if(forbidden.status!==403)throw new Error('Cross-tenant isolation check returned '+forbidden.status);
  console.log('PASS cross-tenant isolation');
  console.log('SMOKE_CHECKS_COMPLETE');
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
