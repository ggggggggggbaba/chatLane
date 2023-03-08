import requests
import json
import os
import time

params = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 128,
}
proxies = {
    "http": os.environ["http_proxy"],
    "https": os.environ["http_proxy"]
}
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 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",
    "Connection": "close",
    # "User-Agent":"OpenAI/v1 PythonBindings/0.27.0"
}

page = ''
while page == '':
    try:
        page = requests.post(url="https://api.openai.com/v1/chat/completions", headers=headers, proxies=proxies,
                          data=bytes(json.dumps(params), encoding="utf-8"), verify=False)
        break
    except:
        print("Connection refused by the server..")
        print("Let me sleep for 5 seconds")
        print("ZZzzzz...")
        time.sleep(5)
        print("Was a nice sleep, now let me continue...")
        continue
print(page.text)
