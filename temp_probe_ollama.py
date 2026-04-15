import json
import urllib.request
import urllib.error

urls = [
    'http://127.0.0.1:11434/v1/chat/completions',
    'http://127.0.0.1:11434/api/generate',
]

for u in urls:
    print('POST', u)
    body = json.dumps({
        'model': 'qwen2.5-coder:14b',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'temperature': 0.2,
        'max_tokens': 10,
    }).encode('utf-8')
    req = urllib.request.Request(u, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print('status', r.status)
            print(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print('ERROR', e.code, e.reason)
        print(e.read().decode('utf-8', errors='replace'))
    except Exception as e:
        print(type(e).__name__, e)
