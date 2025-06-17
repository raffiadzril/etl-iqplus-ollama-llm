import requests
import json
import re

TOGETHER_API_KEY = "4c5b75b56495e70bfbc07e2bb033a0f752585d0797fa366fffb0d2626a51911b"
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def test_together_api():
    headline = "HYGN: HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025"
    content = """HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025.
IQPlus, (12/6) - PT Ecocare Indo Pasifik Tbk. (HYGN) akan membagikan Dividen tunai untuk tahun buku 2024.

Vincent Yunanda Direktur utama HYGN dalam keterangan tertulisnya Kamis (12/6) menuturkan bahwa pembagian dividen ini sesuai dengan keputusan RUPS Tahunan yang digelar pada tanggal 10 Juni 2025 yaitu sebesar Rp6.060.000.000 atau Rp2,4 per saham."""
    
    prompt = f"""
Berikut adalah berita pasar modal:

Judul: {headline}

Isi:
{content}

Tolong analisis berita ini dan berikan output dalam format JSON seperti ini:

{{
  "sentiment": "<positive/negative/neutral>",
  "confidence": <nilai antara 0 dan 1>,
  "reasoning": "<alasan singkat mengapa sentimen ini>",
  "summary": "<ringkasan lengkap dari berita tanpa dipotong, maksimal 3 kalimat>",
  "tickers": ["<kode saham jika ada>"]
}}

Output hanya JSON. Jangan tambahkan penjelasan apa pun di luar itu.
"""

    body = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": "Kamu adalah analis berita pasar modal yang membantu memberikan ringkasan dan analisis sentimen."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=body, timeout=30)
        print("Status code:", response.status_code)
        
        if response.status_code == 200:
            result = response.json()
            content_response = result["choices"][0]["message"]["content"]
            print("Raw response:")
            print(content_response)
            print("\n" + "="*50)
            
            try:
                data = json.loads(content_response)
                print("Parsed JSON:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                print(f"\nField summary ada: {'summary' in data}")
                if 'summary' in data:
                    print(f"Summary: {data['summary']}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                # Try to extract JSON with regex
                match = re.search(r'\{.*\}', content_response, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(0))
                        print("Extracted JSON:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    except:
                        print("Failed to extract JSON even with regex")
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_together_api()
