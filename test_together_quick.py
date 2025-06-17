import requests
import json

TOGETHER_API_KEY = "4c5b75b56495e70bfbc07e2bb033a0f752585d0797fa366fffb0d2626a51911b"
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

body = {
    "model": "meta-llama/Llama-3-8b-chat-hf",
    "messages": [
        {"role": "user", "content": "Say hello in JSON format like {\"message\": \"hello\"}"}
    ],
    "max_tokens": 50,
    "temperature": 0.1
}

try:
    response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=body, timeout=30)
    print("Status:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("Success:", result["choices"][0]["message"]["content"])
    else:
        print("Error:", response.text)
except Exception as e:
    print("Exception:", str(e))
