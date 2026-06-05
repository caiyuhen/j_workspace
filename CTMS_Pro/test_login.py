import urllib.request
import json
import urllib.error
import time

url = 'http://127.0.0.1:8898/api/v1/auth/login'
data = json.dumps({'username': 'admin', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:8899'})
try:
    with urllib.request.urlopen(req, timeout=5) as f:
        print("Success:", f.getcode())
        print(f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Other error:", e)
