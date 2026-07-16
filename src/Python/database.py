import math
import uuid
import json
import firebase_admin
import os;
from firebase_admin import credentials
from firebase_admin import db

current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = os.path.join(current_dir, "..", "env_Files")
# 2. Join that directory path with your JSON file name
json_path = os.path.join(current_dir, "stockml-usertable-firebase-Key.json")


with open(os.path.join(current_dir, "firebase_url.json"), 'r') as f:
    firebase_url_data = json.load(f)
    database_url = firebase_url_data.get("url")


cred = credentials.Certificate(json_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })



results_cache = {}

def save_results(data: dict) -> str:
    res_id = str(uuid.uuid4())
    results_cache[res_id] = _clean(data)
    return res_id

def get_results(res_id: str):
    return results_cache.get(res_id)

def _clean(obj):
    if isinstance(obj, list): return [_clean(x) for x in obj]
    if isinstance(obj, dict): return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, float):
        return 0.0 if (math.isnan(obj) or math.isinf(obj)) else obj
    return obj

def upload_ML_Prob_To_Firebase(user_id: str, ticker: str, probability: float):
    try:
        # The path stops exactly at the ticker. The ticker IS the absolute key.
        ref = db.reference(f'tickers/{ticker.upper()}')
        
        # This completely overwrites the entire ticker block. 
        # Whoever owned it before is erased, and the new user takes ownership.
        ref.set({
            "user_id": user_id,
            "probability": float(probability)
        })
        
        print(f"Ticker {ticker.upper()} is now exclusively held by {user_id} with probability {probability}")
        return True

    except Exception as e:
        print(f"An error occurred while uploading to Realtime DB: {e}")
        return False