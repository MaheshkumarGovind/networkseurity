from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

## configuration of the Data Ingestion Config
from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact
import os
import sys
import numpy as np
import pandas as pd
import pymongo
from typing import List
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv

load_dotenv()
MONGO_DB_URL = os.getenv("MONGO_DB_URL")


class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def export_collection_as_dataframe(self):
        """
        Read data from mongodb
        """
        try:
            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name
            
            logging.info(f"Connecting to MongoDB: {database_name}.{collection_name}")
            
            # Check if MONGO_DB_URL is loaded
            if not MONGO_DB_URL:
                raise ValueError("MONGO_DB_URL is not set in environment variables")
            
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
            collection = self.mongo_client[database_name][collection_name]
            
            # Check if collection exists and has data
            document_count = collection.count_documents({})
            logging.info(f"Found {document_count} documents in collection")
            
            if document_count == 0:
                raise ValueError(
                    f"No data found in MongoDB collection: {database_name}.{collection_name}\n"
                    f"Please run 'python push_data.py' to insert data into MongoDB first."
                )

            df = pd.DataFrame(list(collection.find()))
            
            logging.info(f"DataFrame created with shape: {df.shape}")
            
            if "_id" in df.columns.to_list():
                df = df.drop(columns=["_id"], axis=1)
            
            df.replace({"na": np.nan}, inplace=True)
            
            logging.info(f"Data export completed. Final DataFrame shape: {df.shape}")
            return df
            
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def export_data_into_feature_store(self, dataframe: pd.DataFrame):
        try:
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            
            logging.info(f"Exporting dataframe with shape {dataframe.shape} to feature store")
            
            # Creating folder
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(feature_store_file_path, index=False, header=True)
            
            logging.info(f"Data exported to feature store at: {feature_store_file_path}")
            return dataframe
            
        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def split_data_as_train_test(self, dataframe: pd.DataFrame):
        try:
            logging.info(f"Starting train-test split for dataframe with shape: {dataframe.shape}")
            
            # Validate dataframe before splitting
            if dataframe.shape[0] == 0:
                raise ValueError("Cannot split empty dataframe. No data available for training.")
            
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )
            logging.info("Performed train test split on the dataframe")
            logging.info(f"Train set shape: {train_set.shape}, Test set shape: {test_set.shape}")

            logging.info(
                "Exited split_data_as_train_test method of Data_Ingestion class"
            )
            
            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)
            
            logging.info(f"Exporting train and test file path.")
            
            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )

            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )
            logging.info(f"Exported train and test file path.")

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    def initiate_data_ingestion(self):
        try:
            logging.info("Starting data ingestion process")
            
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
            raise NetworkSecurityException(e, sys)