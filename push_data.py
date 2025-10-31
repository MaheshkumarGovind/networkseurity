import os
import sys
import json
from pathlib import Path

# Get the absolute path of the current file's directory
current_dir = Path(__file__).parent.absolute()
# Add to Python path
sys.path.insert(0, str(current_dir))

# Debug: Print paths
print(f"Current directory: {current_dir}")
print(f"networksecurity folder exists: {(current_dir / 'networksecurity').exists()}")

from dotenv import load_dotenv
import pandas as pd
import pymongo
import certifi

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

load_dotenv()
MONGO_DB_URL = os.getenv("MONGO_DB_URL")

class NetworkDataExtract():
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def csv_to_json_convertor(self, file_path):
        try:
            data = pd.read_csv(file_path)
            data.reset_index(drop=True, inplace=True)
            records = list(json.loads(data.T.to_json()).values())
            return records
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def insert_data_mongodb(self, records, database, collection):
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL, tlsCAFile=certifi.where())
            db = self.mongo_client[database]
            coll = db[collection]
            coll.insert_many(records)
            return len(records)
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
if __name__=='__main__':
    FILE_PATH = "Network_Data/phisingData.csv"
    DATABASE = "MAHESH"
    COLLECTION = "NetworkData"
    
    networkobj = NetworkDataExtract()
    records = networkobj.csv_to_json_convertor(file_path=FILE_PATH)
    print(f"First 5 records: {records[:5]}")
    no_of_records = networkobj.insert_data_mongodb(records, DATABASE, COLLECTION)
    print(f"Inserted {no_of_records} records successfully!")