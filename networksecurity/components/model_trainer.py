import os
import sys

from networksecurity.exception.exception import NetworkSecurityException 
from networksecurity.logging.logger import logging

from networksecurity.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact
from networksecurity.entity.config_entity import ModelTrainerConfig

from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.utils.main_utils.utils import save_object,load_object
from networksecurity.utils.main_utils.utils import load_numpy_array_data,evaluate_models
from networksecurity.utils.ml_utils.metric.classification_metric import get_classification_score

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
import mlflow
from urllib.parse import urlparse

import dagshub
# Fixed: Set consistent URIs and auth for YOUR repo (replace YOUR_DAGSHUB_TOKEN with actual token)
#os.environ["MLFLOW_TRACKING_URI"] = "https://dagshub.com/MaheshkumarGovind/networkseurity.mlflow"
#os.environ["MLFLOW_TRACKING_USERNAME"] = "MaheshkumarGovind"
#os.environ["MLFLOW_TRACKING_PASSWORD"] = "YOUR_DAGSHUB_TOKEN"  # Generate at https://dagshub.com/user/settings/tokens
mlflow.set_registry_uri("https://dagshub.com/MaheshkumarGovind/networkseurity.mlflow")
dagshub.init(repo_owner='MaheshkumarGovind', repo_name='networkseurity', mlflow=True)


class ModelTrainer:
    def __init__(self,model_trainer_config:ModelTrainerConfig,data_transformation_artifact:DataTransformationArtifact):
        try:
            self.model_trainer_config=model_trainer_config
            self.data_transformation_artifact=data_transformation_artifact
        except Exception as e:
            raise NetworkSecurityException(e,sys)
        
    def track_mlflow(self,best_model,classificationmetric,X_data_sample):
        try:
            tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
            with mlflow.start_run():
                f1_score=classificationmetric.f1_score
                precision_score=classificationmetric.precision_score
                recall_score=classificationmetric.recall_score
                
                mlflow.log_metric("f1_score",f1_score)
                mlflow.log_metric("precision",precision_score)
                mlflow.log_metric("recall_score",recall_score)
                
                # Create input example from sample data
                input_example = X_data_sample[:5] if len(X_data_sample) >= 5 else X_data_sample
                
                # Log model with signature and input example (fixes warnings)
                # Fixed: Use 'name' instead of deprecated 'artifact_path'
                if tracking_url_type_store != "file":
                    mlflow.sklearn.log_model(
                        best_model, 
                        name="model",  # Fixed: Use 'name' param
                        registered_model_name=str(type(best_model).__name__),
                        input_example=input_example
                    )
                else:
                    mlflow.sklearn.log_model(
                        best_model, 
                        name="model",  # Fixed: Use 'name' param
                        input_example=input_example
                    )
        except Exception as e:
            logging.error(f"MLflow tracking failed: {e}")
            # Fallback: Save locally without MLflow
            local_path = f"artifacts/model_{type(best_model).__name__}.pkl"
            save_object(local_path, best_model)
            logging.info(f"Model saved locally: {local_path}")

        
    def train_model(self,X_train,y_train,x_test,y_test):
        models = {
                "Random Forest": RandomForestClassifier(verbose=1),
                "Decision Tree": DecisionTreeClassifier(),
                "Gradient Boosting": GradientBoostingClassifier(verbose=1),
                "Logistic Regression": LogisticRegression(verbose=1),
                "AdaBoost": AdaBoostClassifier(),
            }
        params={
            "Decision Tree": {
                'criterion':['gini', 'entropy', 'log_loss'],
                # 'splitter':['best','random'],
                # 'max_features':['sqrt','log2'],
            },
            "Random Forest":{
                # 'criterion':['gini', 'entropy', 'log_loss'],
                
                # 'max_features':['sqrt','log2',None],
                'n_estimators': [8,16,32,128,256]
            },
            "Gradient Boosting":{
                # 'loss':['log_loss', 'exponential'],
                'learning_rate':[.1,.01,.05,.001],
                'subsample':[0.6,0.7,0.75,0.85,0.9],
                # 'criterion':['squared_error', 'friedman_mse'],
                # 'max_features':['auto','sqrt','log2'],
                'n_estimators': [8,16,32,64,128,256]
            },
            "Logistic Regression":{},
            "AdaBoost":{
                'learning_rate':[.1,.01,.001],
                'n_estimators': [8,16,32,64,128,256]
            }
            
        }
        model_report:dict=evaluate_models(X_train=X_train,y_train=y_train,X_test=x_test,y_test=y_test,
                                          models=models,param=params)
        
        ## To get best model score from dict
        # Handle both dict and numeric values in model_report
        best_model_score = None
        best_model_name = None
        
        for model_name, score_or_dict in model_report.items():
            # If the value is a dict, extract the score (assuming key like 'test_score' or similar)
            if isinstance(score_or_dict, dict):
                current_score = score_or_dict.get('test_score', score_or_dict.get('score', 0))
            else:
                current_score = score_or_dict
            
            if best_model_score is None or current_score > best_model_score:
                best_model_score = current_score
                best_model_name = model_name
        best_model = models[best_model_name]
        y_train_pred=best_model.predict(X_train)

        classification_train_metric=get_classification_score(y_true=y_train,y_pred=y_train_pred)
        
        y_test_pred=best_model.predict(x_test)
        classification_test_metric=get_classification_score(y_true=y_test,y_pred=y_test_pred)
        
        ## Track the experiements with mlflow (log ONCE with test metrics for final eval)
        self.track_mlflow(best_model,classification_test_metric,x_test)
        
        # Optional: Log train metrics in a nested run if needed
        # with mlflow.start_run(nested=True):
        #     self.track_mlflow(best_model, classification_train_metric, X_train)  # No model log here

        preprocessor = load_object(file_path=self.data_transformation_artifact.transformed_object_file_path)
            
        model_dir_path = os.path.dirname(self.model_trainer_config.trained_model_file_path)
        os.makedirs(model_dir_path,exist_ok=True)

        Network_Model=NetworkModel(preprocessor=preprocessor,model=best_model)
        # BUGFIX: Changed NetworkModel to Network_Model (the instance, not the class)
        save_object(self.model_trainer_config.trained_model_file_path,obj=Network_Model)
        
        #model pusher (fixed: use dynamic path instead of hardcoded)
        # save_object("final_model/model.pkl",best_model)  # Commented out; use artifact path
        
        ## Model Trainer Artifact
        model_trainer_artifact=ModelTrainerArtifact(trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                             train_metric_artifact=classification_train_metric,
                             test_metric_artifact=classification_test_metric
                             )
        logging.info(f"Model trainer artifact: {model_trainer_artifact}")
        return model_trainer_artifact
        
    def initiate_model_trainer(self)->ModelTrainerArtifact:
        try:
            train_file_path = self.data_transformation_artifact.transformed_train_file_path
            test_file_path = self.data_transformation_artifact.transformed_test_file_path

            #loading training array and testing array
            train_arr = load_numpy_array_data(train_file_path)
            test_arr = load_numpy_array_data(test_file_path)

            x_train, y_train, x_test, y_test = (
                train_arr[:, :-1],
                train_arr[:, -1],
                test_arr[:, :-1],  # FIXED: was test_arr[:, -1]
                test_arr[:, -1],
            )

            model_trainer_artifact=self.train_model(x_train,y_train,x_test,y_test)
            return model_trainer_artifact

            
        except Exception as e:
            raise NetworkSecurityException(e,sys)