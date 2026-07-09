import httpx
import json

payload = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "tools": [
        {
            "type": "bash_20241022",
            "name": "bash"
        }
    ],
    "messages": [
        {
            "role": "user",
            "content": "run `ls` in bash"
        }
    ]
}

resp = httpx.post(
    "http://127.0.0.1:4000/v1/messages",
    json=payload,
    headers={
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "computer-use-2024-10-22",
        "Authorization": "Bearer dummy-key"
    }
)
print(resp.status_code)
print(json.dumps(resp.json(), indent=2))
