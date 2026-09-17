import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/enfycon-inc/ATS_DOCKERREPO/actions/runs?per_page=3")
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for run in data['workflow_runs']:
            print(f"Name: {run['name']}, Status: {run['status']}, Conclusion: {run['conclusion']}, Created: {run['created_at']}")
except Exception as e:
    print(e)
