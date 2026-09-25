import requests

payload = {'username': 'test_user', 'password': 'secure_password'}
response = requests.post('https://httpbin.org', data=payload)

print(response.status_code)
