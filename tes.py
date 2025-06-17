import requests
import json
import re

TOGETHER_API_KEY = "4c5b75b56495e70bfbc07e2bb033a0f752585d0797fa366fffb0d2626a51911b"
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def build_prompt(headline, content):
    return f"""
Berikut adalah berita pasar modal:

Judul: {headline}

Isi:
{content}

Tolong analisis berita ini dan berikan output dalam format JSON seperti ini:

{{
  "sentimen": "<positif/negatif/netral>",
  "keyakinan": <nilai antara 0 dan 1>,
  "alasan": "<alasan singkat mengapa sentimen ini>",
  "ringkasan": "<ringkasan lengkap dari berita tanpa dipotong, maksimal 3 kalimat>",
  "tickers": ["<kode saham jika ada>"]
}}

Output hanya JSON. Jangan tambahkan penjelasan apa pun di luar itu.
"""

def extract_ticker_from_headline(headline):
    match = re.match(r"^([A-Z]{3,5}):", headline)
    return [match.group(1)] if match else []

def analyze_news(headline, content):
    prompt = build_prompt(headline, content)
    
    body = {
        "model": "meta-llama/Llama-3-8b-chat-hf",  # Ganti jika kamu ingin model lain yang didukung
        "messages": [
            {"role": "system", "content": "Kamu adalah analis berita pasar modal yang membantu memberikan ringkasan dan analisis sentimen."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=body)
    
    print("Status code:", response.status_code)
    print("🔹 Raw Output:\n", response.text)

    if response.status_code != 200:
        return {"error": f"Gagal request ke Together API: {response.status_code}"}

    try:
        result_text = response.json()["choices"][0]["message"]["content"]
        result = json.loads(result_text)
        result["tickers"] = extract_ticker_from_headline(headline)
        return result
    except Exception as e:
        return {"error": f"❌ Gagal parsing JSON dari LLM.\nRaw output:\n{result_text}"}

# Contoh data
headline = "HYGN: HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025"
content = """HYGN AKAN BAGIKAN DIVIDEN PADA 11 JULI 2025.
IQPlus, (12/6) - PT Ecocare Indo Pasifik Tbk. (HYGN) akan membagikan Dividen tunai untuk tahun buku 2024.

Vincent Yunanda Direktur utama HYGN dalam keterangan tertulisnya Kamis (12/6) menuturkan bahwa pembagian dividen ini sesuai dengan keputusan RUPS Tahunan yang digelar pada tanggal 10 Juni 2025 yaitu sebesar Rp6.060.000.000 atau Rp2,4 per saham.

Adapun Cum dan Ex Dividen di Pasar Reguler dan Negosiasi akan dilakukan pada tanggal 18 Juni dan 19 Juni 2025 sementara itu Cum dan Ex Dividen di Pasar Tunai pada 20 Juni dan 23 Juni 2025.

Sementara itu daftar Pemegang Saham yang berhak pada tanggal 20 Juni 2025 (recording date) dan pembayaran dividen 32,5% dari Laba Bersih jatuh pada tanggal 11 Juli 2025."""

# Jalankan analisis
hasil = analyze_news(headline, content)

print("\n✅ Hasil Analisis:")
print(json.dumps(hasil, indent=2, ensure_ascii=False))
