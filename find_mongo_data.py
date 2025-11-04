from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_DB_URL')
client = MongoClient(uri)

print("="*70)
print("SEARCHING FOR YOUR DATA IN MONGODB")
print("="*70)

for db_name in client.list_database_names():
    if db_name in ['admin', 'local', 'config']:
        continue
    
    print(f"\n📁 Database: {db_name}")
    db = client[db_name]
    
    for coll_name in db.list_collection_names():
        count = db[coll_name].count_documents({})
        print(f"   📊 Collection: {coll_name} → {count} documents")
        
        if count > 0:
            sample = db[coll_name].find_one()
            print(f"      Sample columns: {list(sample.keys())}")

print("\n" + "="*70)
print("Current config is looking for:")
print(f"   Database: Mahesh")
print(f"   Collection: NetworkData")
print("="*70)