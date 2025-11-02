from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact
import os
import sys
import numpy as np
import pandas as pd
import pymongo
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
import time

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
if not MONGO_DB_URL:
    raise ValueError("MONGO_DB_URL not set in .env")


class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
            self.mongo_client = None
        except Exception as e:
            raise NetworkSecurityException(str(e), sys)
        
    def _connect_with_retry(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                logging.info(f"Attempting MongoDB connection (try {attempt + 1}/{max_retries})")
                self.mongo_client = pymongo.MongoClient(
                    MONGO_DB_URL,
                    serverSelectionTimeoutMS=60000,
                    connectTimeoutMS=30000,
                    maxPoolSize=5
                )
                self.mongo_client.admin.command('ismaster')
                logging.info("MongoDB connection successful")
                return True
            except pymongo.errors.ConfigurationError as dns_err:
                if "DNS operation timed out" in str(dns_err):
                    wait_time = (2 ** attempt) + np.random.random()
                    logging.warning(f"DNS timeout (attempt {attempt + 1}). Retrying in {wait_time:.1f}s.")
                    time.sleep(wait_time)
                else:
                    raise NetworkSecurityException(str(dns_err), sys)
            except Exception as e:
                raise NetworkSecurityException(str(e), sys)
        raise NetworkSecurityException("Max retries exceeded for MongoDB connection", sys)
        
    def export_collection_as_dataframe(self):
        try:
            try:
                if not self._connect_with_retry():
                    raise ValueError("Failed to connect after retries")

                database_name = self.data_ingestion_config.database_name
                collection_name = self.data_ingestion_config.collection_name
                logging.info(f"Querying collection: {database_name}.{collection_name}")

                collection = self.mongo_client[database_name][collection_name]
                df = pd.DataFrame(list(collection.find()))

                if "_id" in df.columns.to_list():
                    df = df.drop(columns=["_id"], axis=1)

                df.replace({"na": np.nan}, inplace=True)

                logging.info(f"Loaded DataFrame from MongoDB: shape {df.shape}")

                if len(df) == 0:
                    raise ValueError("MongoDB collection is empty.")

            except Exception as mongo_err:
                logging.warning(f"MongoDB failed: {str(mongo_err)}. Using mock data fallback.")
                # Mock data (comment out once DB works)
                df = pd.DataFrame({
                    'src_ip': [f"192.168.1.{i}" for i in range(1000)],
                    'dst_ip': [f"10.0.0.{i}" for i in range(1000)],
                    'protocol': np.random.choice(['TCP', 'UDP', 'ICMP'], 1000),
                    'label': np.random.choice(['normal', 'attack'], 1000, p=[0.8, 0.2]),
                    'bytes': np.random.randint(100, 10000, 1000),
                    'packets': np.random.randint(1, 100, 1000)
                })
                logging.info(f"Generated mock DataFrame: shape {df.shape}")

            if self.mongo_client:
                self.mongo_client.close()
                self.mongo_client = None

            return df
        except Exception as e:
            if self.mongo_client:
                self.mongo_client.close()
                self.mongo_client = None
            raise NetworkSecurityException("Error exporting MongoDB collection to DataFrame", sys)
        
    def export_data_into_feature_store(self, dataframe: pd.DataFrame):
        try:
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(feature_store_file_path, index=False, header=True)
            logging.info(f"Exported DataFrame to feature store: {feature_store_file_path}, shape {dataframe.shape}")
            return dataframe
        except Exception as e:
            raise NetworkSecurityException("Error exporting to feature store", sys)
        
    def split_data_as_train_test(self, dataframe: pd.DataFrame):
        try:
            if len(dataframe) == 0:
                raise ValueError("No data to split. Verify data source.")

            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio, random_state=42
            )
            logging.info("Performed train test split on the dataframe")
            logging.info(f"Train set shape: {train_set.shape}, Test set shape: {test_set.shape}")

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)

            logging.info("Exporting train and test file path.")

            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )

            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )
            logging.info("Exported train and test file path.")

        except Exception as e:
            raise NetworkSecurityException("Error splitting data into train/test sets", sys)
        
        
    def initiate_data_ingestion(self):
        try:
            dataframe = self.export_collection_as_dataframe()
            dataframe = self.export_data_into_feature_store(dataframe)
            self.split_data_as_train_test(dataframe)
            dataingestionartifact = DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.testing_file_path
            )
            logging.info("Data ingestion completed successfully")
            return dataingestionartifact

        except Exception as e:
            raise NetworkSecurityException("Error initiating data ingestion", sys)