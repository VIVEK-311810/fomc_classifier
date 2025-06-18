from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
EXCEL_PATH = os.getenv("EXCEL_PATH", "./data/Sentiment&Attributes_Classification.xlsx")
LABEL_COLUMNS = ["Sentiment", "Economic Growth", "Employment Growth",
                 "Inflation", "Medium Term Rate", "Policy Rate"]
MAX_LENGTH = 128

# Hugging Face Model IDs
HUGGINGFACE_MODELS = {
    "Sentiment": "Vk311810/fomc_sentiment_classifier",
    "Economic Growth": "Vk311810/fomc-economic_growth-classifier",
    "Employment Growth": "Vk311810/fomc-employment_growth-classifier",
    "Inflation": "Vk311810/fomc-inflation-classifier",
    "Medium Term Rate": "Vk311810/fomc-medium_rate-classifier",
    "Policy Rate": "Vk311810/fomc-policy_rate-classifier"
}

# Label mappings (from your Gradio code)
label_maps = {
    "Sentiment": {"Positive": 0, "Neutral": 1, "Negative": 2},
    "Economic Growth": {"UP": 0, "Down": 1, "Flat": 2},
    "Employment Growth": {"UP": 0, "Down": 1, "Flat": 2},
    "Inflation": {"UP": 0, "Down": 1, "Flat": 2},
    "Medium Term Rate": {"Hawk": 0, "Dove": 1},
    "Policy Rate": {"Raise": 0, "Flat": 1, "Lower": 2}
}

reverse_label_maps = {
    label: {v: k for k, v in mapping.items()}
    for label, mapping in label_maps.items()
}

# Pydantic models for API
class TextInput(BaseModel):
    text: str

class ClassificationResult(BaseModel):
    sentiment: Dict[str, Any]
    economic_growth: Dict[str, Any]
    employment_growth: Dict[str, Any]
    inflation: Dict[str, Any]
    medium_term_rate: Dict[str, Any]
    policy_rate: Dict[str, Any]

class HistoricalStatement(BaseModel):
    year: int
    month: int
    month_year: str
    statement_content: str
    actual_values: Optional[Dict[str, str]] = None

# Initialize FastAPI app
app = FastAPI(
    title="FOMC Statement Classifier API",
    description="API for classifying FOMC statements using fine-tuned FinBERT models",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and data
models = {}
tokenizers = {}
df = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_excel_data():
    """Load Excel data with historical FOMC statements"""
    global df
    try:
        if os.path.exists(EXCEL_PATH):
            df = pd.read_excel(EXCEL_PATH)
            # Convert date to proper format
            df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
            df["year"] = df["Date"].dt.year
            df["month"] = df["Date"].dt.month
            df["month_year"] = df["Date"].dt.strftime("%b %Y")
            # Ensure statement_content is string type
            df["statement_content"] = df["statement_content"].astype(str)
            logger.info(f"Successfully loaded Excel data with {len(df)} records")
            return True
        else:
            logger.warning(f"Excel file not found at {EXCEL_PATH}")
            return False
    except Exception as e:
        logger.error(f"Failed to load Excel file: {str(e)}")
        return False

def load_models():
    """Load all fine-tuned models and tokenizers from Hugging Face"""
    global models, tokenizers
    
    for label, hf_model_id in HUGGINGFACE_MODELS.items():
        try:
            models[label] = AutoModelForSequenceClassification.from_pretrained(hf_model_id)
            tokenizers[label] = AutoTokenizer.from_pretrained(hf_model_id)
            models[label].to(device)
            models[label].eval()
            logger.info(f"Successfully loaded model for {label} from {hf_model_id}")
        except Exception as e:
            logger.error(f"Failed to load model for {label} from {hf_model_id}: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize models and data on startup"""
    logger.info("Starting FOMC Classifier API...")
    logger.info(f"Using device: {device}")
    logger.info(f"Excel path: {EXCEL_PATH}")
    
    load_models()
    load_excel_data()
    
    loaded_models = [label for label in LABEL_COLUMNS if label in models]
    join_str = ", "
    logger.info(f"Loaded models for: {join_str.join(loaded_models)}")
    
    if len(loaded_models) < len(LABEL_COLUMNS):
        missing = set(LABEL_COLUMNS) - set(loaded_models)
        logger.warning(f"Missing models for: {', '.join(missing)}")