import requests

query_params = {'q': 'python', 'page': 2}
response = requests.get('https://httpbin.org', params=query_params)

# This requests: https://httpbin.org?q=python&page=2
print(response.url)
