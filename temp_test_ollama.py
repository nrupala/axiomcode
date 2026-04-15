import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:11434/v1/chat/completions'
body = {
    'model': 'qwen2.5-coder:14b',
    'messages': [{'role': 'user', 'content': 'Hello'}],
    'temperature': 0.2,
    'max_tokens': 10,
}
req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print('status', r.status)
        print(r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code, e.reason)
    print(e.read().decode('utf-8', errors='replace'))
except Exception as e:
    print(type(e).__name__, str(e))
