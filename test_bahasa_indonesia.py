import requests
import json

# Test data
data = {
    "date": "2025-06-16"
}

try:
    print("🔄 Testing transform service dengan prompt Bahasa Indonesia...")
    response = requests.post("http://localhost:5001/transform", 
                           headers={"Content-Type": "application/json"}, 
                           json=data, 
                           timeout=60)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Transform berhasil!")
        print(f"Processed: {result.get('processed_count', 0)} berita")
        print(f"Message: {result.get('message', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test hasil di MongoDB
print("\n🔍 Checking sample result in MongoDB...")
import pymongo

try:
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['iqplus_db']
    collection = db['processed_news']
    
    # Find latest processed document
    latest = collection.find_one({}, {}, sort=[("processed_at", -1)])
    if latest:
        print("Sample terbaru:")
        print(f"Headline: {latest.get('headline', 'N/A')}")
        print(f"Sentiment: {latest.get('sentiment', 'N/A')}")
        print(f"Reasoning: {latest.get('reasoning', 'N/A')}")
        print(f"Summary: {latest.get('summary', 'N/A')[:100]}...")
    else:
        print("No processed data found")
        
    client.close()
    
except Exception as e:
    print(f"MongoDB check error: {e}")
