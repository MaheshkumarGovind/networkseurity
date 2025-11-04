import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()
MONGO_DB_URL = os.getenv("MONGO_DB_URL")
if not MONGO_DB_URL:
    raise ValueError("MONGO_DB_URL not set in .env!")

import pandas as pd
import numpy as np
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging  # Assuming your custom logger

class NetworkDataExtract:
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)
       
    def csv_to_json_convertor(self, file_path):
        try:
            logging.info(f"Loading CSV from: {file_path}")
            data = pd.read_csv(file_path)
            data.reset_index(drop=True, inplace=True)
            records = list(json.loads(data.T.to_json()).values())
            logging.info(f"Converted {len(records)} records from CSV to JSON")
            return records
        except Exception as e:
            raise NetworkSecurityException(e, sys)
       
    def insert_data_mongodb(self, records, database, collection):
        try:
            logging.info(f"Inserting {len(records)} records into {database}.{collection}")
            self.database = database
            self.collection = collection
            self.records = records
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
            self.db = self.mongo_client[self.database]  # Renamed for clarity
            self.coll = self.db[self.collection]
            
            # Check existing count to avoid duplicates
            existing_count = self.coll.count_documents({})
            if existing_count > 0:
                logging.warning(f"Collection already has {existing_count} docs—skipping insert to avoid duplicates.")
                return existing_count
            
            result = self.coll.insert_many(self.records)
            inserted_count = len(result.inserted_ids)
            logging.info(f"Successfully inserted {inserted_count} records!")
            return inserted_count
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        finally:
            if hasattr(self, 'mongo_client'):
                self.mongo_client.close()
                logging.info("MongoDB connection closed.")
       
if __name__ == '__main__':
    FILE_PATH = "Network_Data\\phishingData.csv"
    DATABASE = "MAHESH"  # Fixed: Uppercase to match Atlas DB
    COLLECTION = "NetworkData"
    
    network_obj = NetworkDataExtract()
    records = network_obj.csv_to_json_convertor(file_path=FILE_PATH)
    print(f"Sample record (first): {records[0] if records else 'No records'}")  # Preview
    no_of_records = network_obj.insert_data_mongodb(records, DATABASE, COLLECTION)
    print(f"Total records inserted/available: {no_of_records}")
    print("🎉 Data pushed! Now update config.yaml (database_name: 'MAHESH') and run: python main.py")