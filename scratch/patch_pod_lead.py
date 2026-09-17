import paramiko

HOST = "13.55.100.200"
USER = "ubuntu"
KEY_FILE = r"C:\Users\deb\.ssh\vps_ats_key_lf"

sql = """
DELETE FROM ats.role_permissions
WHERE permission IN ('job:edit', 'job:approve', 'job:reject')
  AND role_id IN (
    SELECT id FROM ats.custom_roles
    WHERE system_role = 'POD_LEAD'
      AND is_system = true
  );
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, key_filename=KEY_FILE)

sftp = client.open_sftp()
with sftp.file('/tmp/patch_pod.sql', 'w') as f:
    f.write(sql)
sftp.close()

command = "docker cp /tmp/patch_pod.sql ats_postgres:/tmp/patch_pod.sql && docker exec ats_postgres psql -U ats_user -d ats_db -f /tmp/patch_pod.sql"
stdin, stdout, stderr = client.exec_command(command)
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
client.close()
