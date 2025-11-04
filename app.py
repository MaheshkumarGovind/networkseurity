import sys
import os
import certifi
import logging
import pandas as pd

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.constant.training_pipeline import (
    DATA_INGESTION_COLLECTION_NAME,
    DATA_INGESTION_DATABASE_NAME,
)

import pymongo

# ======================================
# STEP 1: Load environment variables
# ======================================
load_dotenv()
ca = certifi.where()

# Try both possible env variable names for flexibility
mongo_db_url = os.getenv("MONGODB_URL_KEY") or os.getenv("MONGO_DB_URL")

if not mongo_db_url:
    raise ValueError(
        "❌ Environment variable 'MONGODB_URL_KEY' or 'MONGO_DB_URL' is missing.\n"
        "Please check your .env file and ensure one of these variables is set:\n"
        "MONGODB_URL_KEY=your_mongo_uri\n"
        "or\n"
        "MONGO_DB_URL=your_mongo_uri"
    )

# Log which variable was used
if os.getenv("MONGODB_URL_KEY"):
    logging.info("Using MONGODB_URL_KEY from .env file")
else:
    logging.info("Using MONGO_DB_URL from .env file")

# ======================================
# STEP 2: Connect to MongoDB
# ======================================
try:
    client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
    client.admin.command("ping")
    logging.info("✅ MongoDB connection successful!")
except Exception as e:
    raise NetworkSecurityException(e, sys)

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

# ======================================
# STEP 3: Initialize FastAPI app
# ======================================
app = FastAPI(title="Network Security Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="./templates")

# ======================================
# ROUTES
# ======================================

@app.get("/", tags=["Root"])
async def index():
    """Redirect root URL to Swagger docs"""
    return RedirectResponse(url="/docs")


@app.get("/train", tags=["Model Training"])
async def train_route():
    """Trigger the training pipeline"""
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response(content="✅ Model training completed successfully!", media_type="text/plain")
    except Exception as e:
        raise NetworkSecurityException(e, sys)


@app.post("/predict", tags=["Prediction"])
async def predict_route(request: Request, file: UploadFile = File(...)):
    """Handle file upload for prediction"""
    try:
        df = pd.read_csv(file.file)
        logging.info(f"Received file with shape: {df.shape}")

        # Load preprocessor and model
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")

        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)
        y_pred = network_model.predict(df)

        # Append predictions
        df["predicted_column"] = y_pred
        df.to_csv("prediction_output/output.csv", index=False)

        # Convert to HTML for display
        table_html = df.to_html(classes="table table-striped", index=False)
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})

    except Exception as e:
        raise NetworkSecurityException(e, sys)


# ======================================
# STEP 4: Run the app
# ======================================
if __name__ == "__main__":
    print("🚀 Starting Network Security FastAPI App...")
    app_run(app, host="0.0.0.0", port=8000)
