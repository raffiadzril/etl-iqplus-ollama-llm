#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB Data Monitor - Monitor data di semua collections
"""

from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB connection
MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DB = 'iqplus_db'

def connect_mongo():
    """Connect to MongoDB"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return client, db

def monitor_collections():
    """Monitor semua collections"""
    client, db = connect_mongo()
    
    print("📊 MongoDB Data Monitor")
    print("=" * 50)
    
    collections = ['raw_news', 'processed_news', 'final_news']
    
    for collection_name in collections:
        collection = db[collection_name]
        count = collection.count_documents({})
        
        print(f"\n📁 Collection: {collection_name}")
        print(f"   Total documents: {count}")
        
        if count > 0:
            # Sample document
            sample = collection.find_one()
            print(f"   Sample document keys: {list(sample.keys())}")
            
            # Latest document
            latest = collection.find().sort("_id", -1).limit(1)
            for doc in latest:
                if 'headline' in doc:
                    print(f"   Latest: {doc['headline'][:60]}...")
                if 'extracted_at' in doc:
                    print(f"   Extracted at: {doc['extracted_at']}")
                if 'processed_at' in doc:
                    print(f"   Processed at: {doc['processed_at']}")
                if 'sentiment' in doc:
                    print(f"   Sentiment: {doc['sentiment']} (confidence: {doc.get('confidence', 'N/A')})")
    
    client.close()

def show_latest_news(limit=5):
    """Show latest news dengan semua info"""
    client, db = connect_mongo()
    
    print(f"\n📰 Latest {limit} News from final_news")
    print("=" * 80)
    
    collection = db['final_news']
    
    for i, doc in enumerate(collection.find().sort("_id", -1).limit(limit), 1):
        print(f"\n{i}. {doc.get('headline', 'No headline')}")
        print(f"   Published: {doc.get('published_at', 'N/A')}")
        print(f"   Sentiment: {doc.get('sentiment', 'N/A')} (confidence: {doc.get('confidence', 'N/A')})")
        print(f"   Tickers: {doc.get('tickers', [])}")
        print(f"   Summary: {doc.get('summary', 'N/A')[:100]}...")
        print(f"   Link: {doc.get('link', 'N/A')}")
    
    client.close()

def export_to_json(collection_name='final_news', filename=None):
    """Export collection to JSON"""
    client, db = connect_mongo()
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{collection_name}_{timestamp}.json"
    
    collection = db[collection_name]
    
    # Get all documents
    documents = []
    for doc in collection.find():
        # Convert ObjectId to string
        doc['_id'] = str(doc['_id'])
        documents.append(doc)
    
    # Save to JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Exported {len(documents)} documents to {filename}")
    client.close()
    
    return filename

def main():
    """Main monitoring function"""
    while True:
        print("\n🔍 MongoDB Monitor Options:")
        print("1. Monitor all collections")
        print("2. Show latest news (final_news)")
        print("3. Export collection to JSON")
        print("4. Clear screen and refresh")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            monitor_collections()
        elif choice == '2':
            limit = input("Number of news to show (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            show_latest_news(limit)
        elif choice == '3':
            collection = input("Collection name (default: final_news): ").strip()
            collection = collection if collection else 'final_news'
            filename = input("Output filename (optional): ").strip()
            filename = filename if filename else None
            export_to_json(collection, filename)
        elif choice == '4':
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
