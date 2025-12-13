
# Troubleshooting

## Logging
The log files for Claude Desktop are located at `~/Library/Logs/Claude`. See https://modelcontextprotocol.io/legacy/tools/debugging for more details.

## HTTP Requests
The following Python script will send a simple request to the CiviCRM API endpoint. It may be useful for checking if environment variables are configured properly before involving the LLM.

```python
import json
import httpx

# configure environment variables
base_url = "https://.../civicrm/ajax/api4"
user_key = "your api key here"
site_key = "your site key here"

# construct http request to get the contact with id=2
headers = {
    "X-Requested-With": "XMLHttpRequest",
    "X-Civi-Auth": f"Bearer {user_key}",
    "_authxSiteKey" : f"{site_key}"
}

payload = {"params": json.dumps({
            "where": [["id", "=", 2]],
})}

session = httpx.AsyncClient(timeout=30)
response = await session.post(
    url=f"{base_url}/Contact/get",
    headers=headers,
    data=payload,
)

# display the response
print(f"Response status code: {response.status_code}")
print("Headers: ")
for k, v in response.headers.items():
    print(f"\t{k}:\t{v}")
print("Text: ")
print(json.dumps(json.loads(response.text), indent=2))
```

Copy the script into a `.py` file, fill in the variables at the top, and run with `python3 test_http.py` (remember to source the virtual environment first).