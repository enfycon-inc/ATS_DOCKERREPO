const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
async function main() {
  const users = await prisma.user.findMany({ select: { id: true, email: true, tenantId: true } });
  const branches = await prisma.branchOffice.findMany({ select: { id: true, name: true, tenantId: true } });
  console.log('USERS:', users);
  console.log('BRANCHES:', branches);
}
main().catch(console.error).finally(() => prisma.());
