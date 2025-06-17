#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transform Service untuk IQPlus Financial News
Bertugas menganalisis sentimen dengan Together AI dan menyimpan hasil ke JSON
"""

from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import logging
import os
import time
import requests
import json
import re

app = Flask(__name__)

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
MONGO_DB = 'iqplus_db'
MONGO_COLLECTION_RAW = 'raw_news'
MONGO_COLLECTION_PROCESSED = 'processed_news'
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', '4c5b75b56495e70bfbc07e2bb033a0f752585d0797fa366fffb0d2626a51911b')
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_sentiment_together_ai(headline, content):
    """Analisis sentimen menggunakan Together AI API"""
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"    }
    
    prompt = f"""
Anda adalah analis berita pasar modal Indonesia yang profesional. Analisis berita berikut dan berikan output dalam Bahasa Indonesia yang baik dan benar.

Berita pasar modal:

Judul: {headline}

Isi:
{content}

INSTRUKSI PENTING:
- Gunakan HANYA Bahasa Indonesia yang baik dan benar
- Reasoning harus menjelaskan alasan sentimen dengan jelas dalam Bahasa Indonesia
- Summary harus merangkum berita secara lengkap dalam Bahasa Indonesia
- Jangan gunakan bahasa Inggris sama sekali

Berikan output dalam format JSON seperti ini:

{{
  "sentiment": "<positive/negative/neutral>",
  "confidence": <nilai antara 0 dan 1>,
  "reasoning": "<alasan lengkap mengapa sentimen ini dalam Bahasa Indonesia>",
  "summary": "<ringkasan lengkap berita dalam Bahasa Indonesia, maksimal 3 kalimat>",
  "tickers": ["<kode saham jika ada>"]
}}

Output hanya JSON. Jangan tambahkan penjelasan apa pun di luar itu.
"""

    body = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": "Anda adalah analis berita pasar modal Indonesia yang profesional. Selalu gunakan Bahasa Indonesia yang baik dan benar dalam setiap analisis. Jangan pernah menggunakan bahasa Inggris dalam reasoning dan summary."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    try:
        logger.info(f"🧠 Memproses dengan Together AI: {headline[:50]}...")
        resp = requests.post(TOGETHER_API_URL, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        
        result = resp.json()
        content_response = result["choices"][0]["message"]["content"]
        
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
            
            logger.info(f"✅ Berhasil analisis: sentiment={data.get('sentiment', 'unknown')}")
            return data
            
        except json.JSONDecodeError:
            # Try to extract JSON from response if it's wrapped in text
            match = re.search(r'\{.*\}', content_response, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                # Extract ticker from headline if not found
                if not data.get('tickers') or len(data.get('tickers', [])) == 0:
                    ticker_match = re.match(r'^([A-Z]{3,5}):', headline)
                    if ticker_match:
                        data['tickers'] = [ticker_match.group(1)]
                    else:
                        data['tickers'] = []
                return data
            else:
                raise ValueError("Tidak dapat mengekstrak JSON dari response")
                
    except Exception as e:
        logger.error(f"❌ Error dalam analisis Together AI: {e}")
        # Fallback analysis
        return analyze_sentiment_fallback(headline, content)

def analyze_sentiment_fallback(headline, content):
    """Analisis sentimen sederhana tanpa LLM"""
    positive_words = ['naik', 'tumbuh', 'meningkat', 'profit', 'laba', 'ekspansi', 'investasi', 'positif', 'bagus', 'untung', 'capex', 'bangun', 'baru', 'dividen']
    negative_words = ['turun', 'merosot', 'rugi', 'loss', 'negatif', 'buruk', 'gagal', 'krisis', 'penurunan', 'defisit']
    
    text = f"{headline} {content}".lower()
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.8, 0.5 + (negative_count - positive_count) * 0.1)
    else:
        sentiment = "neutral"
        confidence = 0.6
    
    # Extract tickers (pattern XXXX: di awal headline)
    tickers = []
    ticker_match = re.match(r'^([A-Z]{3,5}):', headline)
    if ticker_match:
        tickers = [ticker_match.group(1)]
    
    # Ringkasan 2-3 kalimat dari isi konten (lebih natural)
    summary = re.sub(r'\s+', ' ', content.strip())  # Hilangkan newline berlebihan
    summary_sentences = re.split(r'(?<=[.!?]) +', summary)
    summary = ' '.join(summary_sentences[:3])  # Maksimal 3 kalimat

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "tickers": tickers,
        "reasoning": f"Analisis fallback: {positive_count} positif, {negative_count} negatif",
        "summary": summary
    }

def get_raw_news_from_mongo(date_str=None):
    """Ambil berita mentah dari MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION_RAW]
    
    if date_str:
        # Filter berdasarkan tanggal
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date() - timedelta(days=1)  # Ambil berita dari hari sebelumnya
        # Query MongoDB untuk berita dari tanggal tersebut
        query = {}  # Bisa ditambahkan filter tanggal jika diperlukan
    else:
        query = {}
    
    berita_list = list(collection.find(query))
    client.close()
    
    # Convert ObjectId to string for JSON serialization
    for berita in berita_list:
        berita['_id'] = str(berita['_id'])
    
    return berita_list

def save_processed_to_json_and_mongo(processed_list, date_str):
    """Simpan hasil processing ke JSON dan MongoDB"""
    
    # Simpan ke JSON file
    output_file = f"/app/data/processed_news_{date_str.replace('-', '')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_list, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"💾 Hasil disimpan ke file: {output_file}")
    
    # Simpan ke MongoDB
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION_PROCESSED]
    
    # Tambahkan timestamp processing
    for item in processed_list:
        item['processed_at'] = datetime.now(JAKARTA_TZ).isoformat()
    
    # Insert ke MongoDB (hapus _id string sebelum insert)
    items_for_mongo = []
    for item in processed_list:
        item_copy = item.copy()
        if '_id' in item_copy and isinstance(item_copy['_id'], str):
            del item_copy['_id']  # Biarkan MongoDB generate _id baru
        items_for_mongo.append(item_copy)
    
    if items_for_mongo:
        result = collection.insert_many(items_for_mongo)
        inserted_count = len(result.inserted_ids)
        logger.info(f"💾 Berhasil simpan {inserted_count} berita ke MongoDB collection: {MONGO_COLLECTION_PROCESSED}")
    else:
        inserted_count = 0
        logger.warning("⚠️ Tidak ada data untuk disimpan ke MongoDB")
    
    client.close()
    
    return output_file, inserted_count

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "transform-llm",
        "timestamp": datetime.now(JAKARTA_TZ).isoformat(),
        "llm_provider": "Together AI"
    })

@app.route('/transform', methods=['POST'])
def transform_news():
    """Endpoint utama untuk transformasi berita"""
    try:
        data = request.get_json()
        date_str = data.get('date', datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d"))
        
        logger.info(f"🎯 Mulai transformasi untuk tanggal: {date_str}")
        
        # Ambil data dari MongoDB
        raw_news_list = get_raw_news_from_mongo(date_str)
        
        if not raw_news_list:
            return jsonify({
                "status": "success",
                "message": "Tidak ada berita untuk diproses",
                "processed_count": 0,
                "date": date_str
            })
        
        logger.info(f"📄 Ditemukan {len(raw_news_list)} berita untuk diproses")
        
        processed_list = []
        
        for berita in raw_news_list:
            try:
                logger.info(f"🔄 Memproses: {berita['headline']}")
                
                # Analisis dengan Together AI
                analysis_result = analyze_sentiment_together_ai(berita['headline'], berita['content'])
                
                # Gabungkan data original dengan hasil analisis
                processed = {
                    **berita,  # Data original
                    **analysis_result  # Hasil analisis
                }
                
                processed_list.append(processed)
                logger.info(f"✅ Berhasil proses: {berita['headline']}")
                
            except Exception as e:
                logger.error(f"❌ Error memproses berita '{berita['headline']}': {e}")
                # Tambahkan dengan error info
                processed = {
                    **berita,
                    "error": str(e),
                    "sentiment": "unknown",
                    "confidence": 0.0,
                    "tickers": [],
                    "reasoning": f"Error: {str(e)}",
                    "summary": f"Error memproses berita: {berita['headline']}"
                }
                processed_list.append(processed)
        
        # Simpan hasil ke JSON dan MongoDB
        output_file, inserted_count = save_processed_to_json_and_mongo(processed_list, date_str)
        
        return jsonify({
            "status": "success",
            "message": f"Berhasil transformasi {len(processed_list)} berita",
            "processed_count": len(processed_list),
            "inserted_count": inserted_count,
            "output_file": output_file,
            "date": date_str
        })
        
    except Exception as e:
        logger.error(f"❌ Error dalam transformasi: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transform/file', methods=['POST'])
def transform_from_file():
    """Endpoint untuk transformasi dari file JSON yang sudah ada"""
    try:
        data = request.get_json()
        input_file = data.get('input_file')
        
        if not input_file or not os.path.exists(input_file):
            return jsonify({"status": "error", "message": "File input tidak ditemukan"}), 400
        
        # Baca dari file JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_news_list = json.load(f)
        
        logger.info(f"📂 Memuat {len(raw_news_list)} berita dari file: {input_file}")
        
        processed_list = []
        
        for berita in raw_news_list:
            try:
                # Analisis dengan Together AI
                analysis_result = analyze_sentiment_together_ai(berita['headline'], berita['content'])
                
                # Gabungkan data original dengan hasil analisis
                processed = {
                    **berita,
                    **analysis_result
                }
                
                processed_list.append(processed)
                logger.info(f"✅ Berhasil proses: {berita['headline']}")
                
            except Exception as e:
                logger.error(f"❌ Error memproses berita '{berita['headline']}': {e}")
                # Tambahkan dengan error info
                processed = {
                    **berita,
                    "error": str(e),
                    "sentiment": "unknown",
                    "confidence": 0.0,
                    "tickers": [],
                    "reasoning": f"Error: {str(e)}",
                    "summary": f"Error memproses berita: {berita['headline']}"
                }
                processed_list.append(processed)
        
        # Generate date string dari nama file atau gunakan tanggal sekarang
        date_str = datetime.now(JAKARTA_TZ).strftime("%Y-%m-%d")
        
        # Simpan hasil
        output_file, inserted_count = save_processed_to_json_and_mongo(processed_list, date_str)
        
        return jsonify({
            "status": "success",
            "message": f"Berhasil transformasi {len(processed_list)} berita dari file",
            "processed_count": len(processed_list),
            "inserted_count": inserted_count,
            "input_file": input_file,
            "output_file": output_file
        })
        
    except Exception as e:
        logger.error(f"❌ Error dalam transformasi file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Transform Service dengan Together AI dimulai...")
    logger.info(f"🔗 Together AI API URL: {TOGETHER_API_URL}")
    logger.info(f"📊 MongoDB URI: {MONGO_URI}")
    app.run(host='0.0.0.0', port=5001, debug=False)
