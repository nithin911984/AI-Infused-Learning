import requests

response = requests.get('https://github.com')

# 1. Print the status code to check for errors (e.g., 404, 500, 403)
print(f"Status Code: {response.status_code}")

# 2. Print the raw content to see what the server actually sent
print("Raw Response Text:")
print(response.text)

# 3. Only parse if you are sure it's valid JSON
try:
    data = response.json()
    print(data)
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON! The server did not return valid JSON.")

