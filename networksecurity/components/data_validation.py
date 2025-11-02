import os
import sys
from pathlib import Path
import pandas as pd
from scipy.stats import ks_2samp

from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity   import DataValidationConfig
from networksecurity.exception.exception    import NetworkSecurityException
from networksecurity.logging.logger         import logging
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file
from networksecurity.constant.training_pipeline import SCHEMA_FILE_PATH   # data_schema/schema.yaml

class DataValidation:
    def __init__(self,
                 data_ingestion_artifact: DataIngestionArtifact,
                 data_validation_config: DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config  = data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    # ------------------------------------------------------------------
    @staticmethod
    def read_data(file_path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    # ------------------------------------------------------------------
    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            # columns field is now a DICT (not a list) -> get keys directly
            required_cols = list(self._schema_config['columns'].keys())
            required = len(required_cols)
            actual   = len(dataframe.columns)

            logging.info("Required columns: %d | Actual: %d", required, actual)
            logging.info("Expected: %s", required_cols)
            logging.info("Got     : %s", list(dataframe.columns))

            return actual == required
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    # ------------------------------------------------------------------
    def detect_dataset_drift(self,
                             base_df: pd.DataFrame,
                             current_df: pd.DataFrame,
                             threshold: float = 0.05) -> bool:
        try:
            report = {}
            status = True

            for col in base_df.columns:
                d1, d2 = base_df[col], current_df[col]
                stat, p_value = ks_2samp(d1, d2)
                drift_found = p_value <= threshold
                if drift_found:
                    status = False
                report[col] = {
                    "p_value": float(p_value),
                    "drift_status": drift_found
                }

            report_path = Path(self.data_validation_config.drift_report_file_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            write_yaml_file(report_path, report)
            return status
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e

    # ------------------------------------------------------------------
    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            train_path = self.data_ingestion_artifact.trained_file_path
            test_path  = self.data_ingestion_artifact.test_file_path

            train_df = self.read_data(train_path)
            test_df  = self.read_data(test_path)

            # 1. column-count check
            if not self.validate_number_of_columns(train_df):
                raise ValueError("Train dataframe column count mismatch.")
            if not self.validate_number_of_columns(test_df):
                raise ValueError("Test dataframe column count mismatch.")

            # 2. drift check
            validation_status = self.detect_dataset_drift(train_df, test_df)

            # 3. save validated files
            for split, df in (("train", train_df), ("test", test_df)):
                out_path = getattr(self.data_validation_config, f"valid_{split}_file_path")
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(out_path, index=False, header=True)

            return DataValidationArtifact(
                validation_status=validation_status,
                valid_train_file_path=self.data_validation_config.valid_train_file_path,
                valid_test_file_path =self.data_validation_config.valid_test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path =None,
                drift_report_file_path =self.data_validation_config.drift_report_file_path,
            )
        except Exception as e:
            raise NetworkSecurityException(e, sys) from e