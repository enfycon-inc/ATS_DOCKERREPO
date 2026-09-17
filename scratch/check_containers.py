import paramiko
import sys
HOST = "13.55.100.200"
USER = "ubuntu"
KEY_FILE = r"C:\Users\deb\.ssh\vps_ats_key_lf"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, key_filename=KEY_FILE)
stdin, stdout, stderr = client.exec_command("docker ps -a")
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
