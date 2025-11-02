from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
import logging

load_dotenv()  # Loads .env
uri = os.getenv("MONGO_DB_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"Testing URI on mobile: {uri[:60]}...")  # Preview (redacted)

try:
    client = MongoClient(
        uri,
        connectTimeoutMS=10000,      # 10s connect
        serverSelectionTimeoutMS=10000  # Quick selection
    )
    # Ping test
    result = client.admin.command('ping')
    logger.info("✅ Connected on mobile! Ping successful.")
    logger.info(f"Server version: {result.get('ok', 'N/A')}")

    # Test your DB/collection (update if different)
    db_name = "networksecurity"  # From your TrainingPipelineConfig
    coll_name = "traffic_data"   # From config
    db = client[db_name]
    coll = db[coll_name]
    count = coll.count_documents({})
    logger.info(f"Collection '{coll_name}' size: {count}")

    # Insert sample network security data if empty
    if count == 0:
        sample_data = [
            {
                "src_ip": f"192.168.1.{i}",
                "dst_ip": "10.0.0.1",
                "protocol": "TCP" if i % 2 == 0 else "UDP",
                "label": "normal" if i < 800 else "attack",
                "bytes": i * 10 + 100,
                "packets": i % 100 + 1
            }
            for i in range(1000)
        ]
        inserted = coll.insert_many(sample_data)
        logger.info(f"Inserted {len(inserted.inserted_ids)} sample records!")

    client.close()
    print("🎉 Success! Now run your pipeline: python main.py")
except Exception as e:
    logger.error(f"❌ Failed: {e}")
    print("Troubleshoot:")
    print("- Check Atlas IP whitelist (add mobile IP from whatismyip.com).")
    print("- Verify replicaSet ID (recopy URI from Atlas).")
    print("- Temp: Allow all IPs in Atlas Network Access (0.0.0.0/0).")