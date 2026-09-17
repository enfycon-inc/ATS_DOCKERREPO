import paramiko
import sys
HOST = "13.55.100.200"
USER = "ubuntu"
KEY_FILE = r"C:\Users\deb\.ssh\vps_ats_key_lf"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, key_filename=KEY_FILE)
client.exec_command("cd /var/www/ats && docker compose -f docker-compose.prod.yml up -d backend_blue frontend_blue")
stdin, stdout, stderr = client.exec_command("cd /var/www/ats && docker compose -f docker-compose.prod.yml rm -f -s -v backend_blue frontend_blue")
print("STDOUT RM:", stdout.read().decode())
print("STDERR RM:", stderr.read().decode())
client.close()
