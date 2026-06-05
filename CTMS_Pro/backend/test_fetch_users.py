import requests
import json

res = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={'username':'jintian@ctms.com','password':'111111'})
data = res.json()
print("Login:", data)

token = data.get('access_token')
if token:
    res = requests.get('http://127.0.0.1:8000/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    print("Users:", res.json())
