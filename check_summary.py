import pymongo
import json

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['iqplus_db']
collection = db['processed_news']

# Find one document and print all fields
doc = collection.find_one()
if doc:
    # Convert ObjectId to string for JSON serialization
    doc['_id'] = str(doc['_id'])
    print("Sample document fields:")
    for key in doc.keys():
        print(f"- {key}")
    
    print("\nFull document:")
    print(json.dumps(doc, indent=2, ensure_ascii=False, default=str))
    
    # Check specifically for summary field
    print(f"\nSummary field exists: {'summary' in doc}")
    if 'summary' in doc:
        print(f"Summary content: {doc.get('summary', 'N/A')}")
else:
    print("No documents found in processed_news collection")

client.close()
