const { PrismaClient } = require('./ats_backend/node_modules/@prisma/client');
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: "postgresql://ats_user:AtsDevPass2024@13.55.100.200:5432/ats_db?schema=ats&options=-csearch_path%3Dats,mass_mail,public"
    }
  }
});

async function main() {
  const user = await prisma.user.findFirst({
    where: { email: 'admin@enfycon.com' }
  });
  console.log('USER:', user);
  if (user && user.roleId) {
     const role = await prisma.$queryRaw`SELECT * FROM ats.custom_roles WHERE id = ${user.roleId}::uuid`;
     console.log('ROLE:', role);
  }
}
main().catch(console.error).finally(() => prisma.$disconnect());
