#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load Service untuk IQPlus Financial News
Bertugas memuat data dari JSON hasil transform ke MongoDB final collection
"""

from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import logging
import os
import json

app = Flask(__name__)

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
MONGO_DB = 'iqplus_db'
MONGO_COLLECTION_PROCESSED = 'processed_news'
MONGO_COLLECTION_FINAL = 'final_news'
MONGO_COLLECTION_ANALYTICS = 'news_analytics'
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_mongo():
    """Connect to MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return client, db

def load_from_json_to_final(json_file_path, target_date=None):
    """Load data dari JSON file ke final collection"""
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"File JSON tidak ditemukan: {json_file_path}")
    
    # Baca data dari JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)
    
    logger.info(f"📂 Memuat {len(processed_data)} data dari: {json_file_path}")
    
    client, db = connect_mongo()
    collection = db[MONGO_COLLECTION_FINAL]
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for data in processed_data:
        try:
            # Cek duplikasi berdasarkan headline dan published_at
            filter_criteria = {
                "headline": data["headline"], 
                "published_at": data["published_at"]
            }
            
            existing = collection.find_one(filter_criteria)
            
            if existing:
                # Update jika ada perubahan di sentiment analysis
                if (existing.get('sentiment') != data.get('sentiment') or 
                    existing.get('confidence') != data.get('confidence')):
                    
                    # Update document
                    data["final_loaded_at"] = datetime.now(JAKARTA_TZ).isoformat()
                    data["processing_date"] = target_date
                    data["updated_at"] = datetime.now(JAKARTA_TZ).isoformat()
                    
                    # Remove _id jika ada
                    if '_id' in data:
                        del data['_id']
                    
                    collection.replace_one(filter_criteria, data)
                    updated += 1
                    logger.info(f"🔄 Updated: {data['headline']}")
                else:
                    skipped += 1
                    logger.info(f"⏭️ Skipped (no changes): {data['headline']}")
            else:
                # Insert new document
                # Remove _id jika ada
                if '_id' in data:
                    del data['_id']
                
                # Tambahkan metadata final
                data["final_loaded_at"] = datetime.now(JAKARTA_TZ).isoformat()
                data["processing_date"] = target_date
                
                collection.insert_one(data)
                inserted += 1
                logger.info(f"💾 Inserted: {data['headline']}")
                
        except Exception as e:
            logger.error(f"❌ Error loading data '{data.get('headline', 'Unknown')}': {e}")
            continue
    
    client.close()
    
    result = {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_processed": len(processed_data)
    }
    
    logger.info(f"🏁 Load completed: {result}")
    return result

def load_from_processed_collection(target_date=None):
    """Load data dari processed collection ke final collection"""
    client, db = connect_mongo()
    
    processed_collection = db[MONGO_COLLECTION_PROCESSED]
    final_collection = db[MONGO_COLLECTION_FINAL]
    
    # Query untuk data yang belum di-load ke final
    query = {}
    if target_date:
        # Bisa ditambahkan filter tanggal jika diperlukan
        pass
    
    processed_data = list(processed_collection.find(query))
    
    if not processed_data:
        logger.warning("🚫 Tidak ada data processed untuk di-load")
        client.close()
        return {"message": "No data to load", "count": 0}
    
    logger.info(f"📊 Memproses {len(processed_data)} data dari processed collection")
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for data in processed_data:
        try:
            # Cek apakah sudah ada di final collection
            filter_criteria = {
                "headline": data["headline"], 
                "published_at": data["published_at"]
            }
            
            existing = final_collection.find_one(filter_criteria)
            
            if existing:
                # Cek apakah ada update pada analysis
                if (existing.get('sentiment') != data.get('sentiment') or 
                    existing.get('confidence') != data.get('confidence') or
                    existing.get('processed_at') != data.get('processed_at')):
                    
                    # Update document
                    data["final_loaded_at"] = datetime.now(JAKARTA_TZ).isoformat()
                    data["processing_date"] = target_date
                    data["updated_at"] = datetime.now(JAKARTA_TZ).isoformat()
                    
                    # Remove _id untuk avoid conflict
                    if '_id' in data:
                        del data['_id']
                    
                    final_collection.replace_one(filter_criteria, data)
                    updated += 1
                    logger.info(f"🔄 Updated: {data['headline']}")
                else:
                    skipped += 1
                    logger.info(f"⏭️ Skipped: {data['headline']}")
            else:
                # Insert new
                # Remove _id untuk avoid conflict
                if '_id' in data:
                    del data['_id']
                
                data["final_loaded_at"] = datetime.now(JAKARTA_TZ).isoformat()
                data["processing_date"] = target_date
                
                final_collection.insert_one(data)
                inserted += 1
                logger.info(f"💾 Inserted: {data['headline']}")
                
        except Exception as e:
            logger.error(f"❌ Error loading '{data.get('headline', 'Unknown')}': {e}")
            continue
    
    client.close()
    
    result = {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_processed": len(processed_data)
    }
    
    logger.info(f"🏁 Load from processed collection completed: {result}")
    return result

def generate_analytics_summary(target_date=None):
    """Generate analytics summary untuk tanggal tertentu"""
    client, db = connect_mongo()
    final_collection = db[MONGO_COLLECTION_FINAL]
    analytics_collection = db[MONGO_COLLECTION_ANALYTICS]
    
    # Query untuk data pada tanggal tertentu
    query = {}
    if target_date:
        query["processing_date"] = target_date
    
    news_data = list(final_collection.find(query))
    
    if not news_data:
        logger.warning("🚫 Tidak ada data untuk analytics")
        client.close()
        return {"message": "No data for analytics"}
    
    # Generate analytics
    total_news = len(news_data)
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    tickers_mentioned = {}
    avg_confidence = 0
    
    for news in news_data:
        # Count sentiments
        sentiment = news.get('sentiment', 'neutral')
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        
        # Count tickers
        tickers = news.get('tickers', [])
        for ticker in tickers:
            if ticker in tickers_mentioned:
                tickers_mentioned[ticker] += 1
            else:
                tickers_mentioned[ticker] = 1
        
        # Sum confidence
        confidence = news.get('confidence', 0)
        avg_confidence += confidence
    
    # Calculate averages
    if total_news > 0:
        avg_confidence = avg_confidence / total_news
    
    # Sort tickers by frequency
    top_tickers = sorted(tickers_mentioned.items(), key=lambda x: x[1], reverse=True)[:10]
    
    analytics_data = {
        "date": target_date,
        "total_news": total_news,
        "sentiment_distribution": sentiment_counts,
        "sentiment_percentage": {
            "positive": round((sentiment_counts["positive"] / total_news) * 100, 2) if total_news > 0 else 0,
            "negative": round((sentiment_counts["negative"] / total_news) * 100, 2) if total_news > 0 else 0,
            "neutral": round((sentiment_counts["neutral"] / total_news) * 100, 2) if total_news > 0 else 0,
        },
        "average_confidence": round(avg_confidence, 3),
        "top_tickers": top_tickers,
        "generated_at": datetime.now(JAKARTA_TZ).isoformat()
    }
    
    # Save analytics
    filter_criteria = {"date": target_date}
    analytics_collection.replace_one(
        filter_criteria, 
        analytics_data, 
        upsert=True
    )
    
    client.close()
    
    logger.info(f"📊 Analytics generated for {target_date}: {total_news} news")
    return analytics_data

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "load-service"})

@app.route('/load/json', methods=['POST'])
def load_from_json():
    """Load data dari JSON file ke final collection"""
    try:
        data = request.get_json()
        json_file = data.get('json_file')
        target_date = data.get('date')
        
        if not json_file:
            return jsonify({"status": "error", "message": "json_file parameter required"}), 400
        
        logger.info(f"🎯 Starting load from JSON: {json_file}")
        
        result = load_from_json_to_final(json_file, target_date)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully loaded data from {json_file}",
            "result": result,
            "json_file": json_file,
            "target_date": target_date
        })
        
    except Exception as e:
        logger.error(f"❌ Error loading from JSON: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/load/processed', methods=['POST'])
def load_from_processed():
    """Load data dari processed collection ke final collection"""
    try:
        data = request.get_json() or {}
        target_date = data.get('date')
        
        logger.info(f"🎯 Starting load from processed collection for date: {target_date}")
        
        result = load_from_processed_collection(target_date)
        
        return jsonify({
            "status": "success",
            "message": "Successfully loaded data from processed collection",
            "result": result,
            "target_date": target_date
        })
        
    except Exception as e:
        logger.error(f"❌ Error loading from processed collection: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/analytics/generate', methods=['POST'])
def generate_analytics():
    """Generate analytics summary"""
    try:
        data = request.get_json() or {}
        target_date = data.get('date')
        
        if not target_date:
            # Default ke kemarin
            yesterday = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).date()
            target_date = yesterday.strftime("%Y-%m-%d")
        
        logger.info(f"📊 Generating analytics for date: {target_date}")
        
        analytics = generate_analytics_summary(target_date)
        
        return jsonify({
            "status": "success",
            "message": f"Analytics generated for {target_date}",
            "analytics": analytics
        })
        
    except Exception as e:
        logger.error(f"❌ Error generating analytics: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        client, db = connect_mongo()
        
        stats = {}
        collections = ['raw_news', 'processed_news', 'final_news', 'news_analytics']
        
        for collection_name in collections:
            collection = db[collection_name]
            count = collection.count_documents({})
            stats[collection_name] = count
        
        client.close()
        
        return jsonify({
            "status": "success",
            "database_stats": stats,
            "checked_at": datetime.now(JAKARTA_TZ).isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
