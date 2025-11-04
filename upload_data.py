from pymongo.mongo_client import MongoClient
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGO_DB_URL')
client = MongoClient(uri)

# Your database and collection (matching your config)
db = client["Mahesh"]
collection = db["NetworkData"]

print("Creating network traffic dataset...")

# Create some realistic network traffic data
data = {
    'src_ip': ['192.168.1.10', '10.0.0.5', '172.16.0.20', '192.168.1.100', '10.0.0.50'] * 200,
    'dst_ip': ['8.8.8.8', '1.1.1.1', '192.168.1.1', '10.0.0.1', '172.16.0.1'] * 200,
    'protocol': ['TCP', 'UDP', 'TCP', 'UDP', 'ICMP'] * 200,
    'bytes': [1500, 800, 2400, 1200, 600] * 200,
    'packets': [10, 5, 15, 8, 3] * 200,
    'label': [0, 1, 0, 1, 0] * 200  # 0=normal, 1=attack
}

df = pd.DataFrame(data)
print(f"Generated DataFrame with {len(df)} rows")

# Convert to records
records = df.to_dict('records')

# Clear existing data
print("Clearing old data...")
collection.delete_many({})

# Insert new data
print("Uploading to MongoDB...")
result = collection.insert_many(records)

print("\n" + "="*60)
print("✅ SUCCESS!")
print("="*60)
print(f"Inserted: {len(result.inserted_ids)} documents")
print(f"Total documents in collection: {collection.count_documents({})}")
print(f"Database: Mahesh")
print(f"Collection: NetworkData")
print("="*60)

# Show a sample
print("\nSample document:")
sample = collection.find_one()
print(sample)