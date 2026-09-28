file_path = r"ats_backend\src\jobs\jobs.service.ts"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("Your delegation request for job ${req.job.jobCode} was accepted.", "Your delegation request for job ${req.job.jobCode} was accepted by ${user?.fullName || user?.email || 'an admin'}.")
code = code.replace("Your delegation request for job ${req.job.jobCode} was rejected.", "Your delegation request for job ${req.job.jobCode} was rejected by ${user?.fullName || user?.email || 'an admin'}.")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)
print("Updated jobs.service.ts")
