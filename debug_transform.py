#!/usr/bin/env python3
import requests
import json
import re
import os

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', '4c5b75b56495e70bfbc07e2bb033a0f752585d0797fa366fffb0d2626a51911b')
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

def analyze_sentiment_together_ai(headline, content):
    """Analisis sentimen menggunakan Together AI API"""
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
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
        print(f"🧠 Memproses dengan Together AI: {headline[:50]}...")
        resp = requests.post(TOGETHER_API_URL, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        
        result = resp.json()
        content_response = result["choices"][0]["message"]["content"]
        
        print("Raw response:")
        print(content_response)
        print("\n" + "="*50 + "\n")
        
        try:
            # Parse JSON response
            data = json.loads(content_response)
            
            # Extract ticker from headline if not found by AI
            if not data.get('tickers') or len(data.get('tickers', [])) == 0:
                ticker_match = re.match(r'^([A-Z]{3,5}):', headline)
                if ticker_match:
                    data['tickers'] = [ticker_match.group(1)]
                else:
                    data['tickers'] = []
            
            print(f"✅ Berhasil analisis: sentiment={data.get('sentiment', 'unknown')}")
            print("Parsed JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Try to extract JSON from response if it's wrapped in text
            match = re.search(r'\{.*\}', content_response, re.DOTALL)
            if match:
                print("Trying to extract JSON with regex...")
                data = json.loads(match.group(0))
                # Extract ticker from headline if not found
                if not data.get('tickers') or len(data.get('tickers', [])) == 0:
                    ticker_match = re.match(r'^([A-Z]{3,5}):', headline)
                    if ticker_match:
                        data['tickers'] = [ticker_match.group(1)]
                    else:
                        data['tickers'] = []
                print("Extracted JSON:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
            else:
                raise ValueError("Tidak dapat mengekstrak JSON dari response")
                
    except Exception as e:
        print(f"❌ Error dalam analisis Together AI: {e}")
        return {"error": str(e)}

# Test with real data
headline = "HYGN: HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025"
content = """HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025.
IQPlus, (12/6) - PT Ecocare Indo Pasifik Tbk. (HYGN) akan membagikan Dividen tunai untuk tahun buku 2024.

Vincent Yunanda Direktur utama HYGN dalam keterangan tertulisnya Kamis (12/6) menuturkan bahwa pembagian dividen ini sesuai dengan keputusan RUPS Tahunan yang digelar pada tanggal 10 Juni 2025 yaitu sebesar Rp6.060.000.000 atau Rp2,4 per saham.

Adapun Cum dan Ex Dividen di Pasar Reguler dan Negosiasi akan dilakukan pada tanggal 18 Juni dan 19 Juni 2025 sementara itu Cum dan Ex Dividen di Pasar Tunai pada 20 Juni dan 23 Juni 2025.

Sementara itu daftar Pemegang Saham yang berhak pada tanggal 20 Juni 2025 (recording date) dan pembayaran dividen 32,5% dari Laba Bersih jatuh pada tanggal 11 Juli 2025."""

result = analyze_sentiment_together_ai(headline, content)
print("\nFinal result:")
print(json.dumps(result, indent=2, ensure_ascii=False))
