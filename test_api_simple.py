#!/usr/bin/env python3
import requests
import json
import os

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def test_api():
    body = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "user", "content": "Hello, please respond with a simple JSON: {\"test\": \"success\"}"}
        ],
        "max_tokens": 100,
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", 
                               headers=headers, json=body, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"Content: {content}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
