# src/Python/scanner_service.py
import pandas as pd
from src.Python.models import StockInfo
from src.Python import analysis_logic as logic
from src.Python import database
import gc,os,joblib
from sklearn.ensemble import RandomForestClassifier
import pandas_ta as ta
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import firebase_admin
from firebase_admin import db
import gc
# Use db from firebase_admin
import os
import pickle
import base64
import gc
import yfinance as yf
import joblib
import database as dbClass

GlobalUserName_Var="testuser"

def run_pipeline(file_obj):
    file_obj.seek(0)
    df = pd.read_csv(file_obj)
    tickers = df['Ticker'].dropna().unique().tolist()
    
    stocks = []
    for t in tickers:
        s = StockInfo(ticker=str(t).strip().upper())
        s.download_all_data()
        if s.close_prices_1y is not None:
            stocks.append(s)

    # These MUST match the paths in your JS fetch calls: get('cup-handle') etc.
    output = {
        "cup-handle": [],
        "double-bottom": [],
        "close-to-150-slow-atr": [],
        "close-to-150-3-atr": [],
        "close-to-200-slow-atr": [],
        "close-to-200-3-atr": [],
        "min-pivots-ready-for-entry": [],
        "max-pivots-ready-for-entry": [],
        "above-from-20-above-2x-atr": [],
        "below-from-20-above-2x-atr": []
    }

    for s in stocks:
        # 1. Get Pivot Data
        h_pivs = logic.find_pivots(s.high_prices_3y, is_high=True)
        l_pivs = logic.find_pivots(s.low_prices_1y, is_high=False)

        # 2. Cup & Handle (Matches JS: if (dates.length > 0))
        
        ch = logic.CupHandleValidator.check_cup_handle(s, h_pivs["Ready"] + h_pivs["NotReady"])
        
        if ch["Bool"]:
            display_data = ch["Dates"]
            output["cup-handle"].append({
                "Stock": s.ticker,
                "Data": display_data 
            })

        # 3. Min/Max Pivots (Matches JS: renderPivots table format)
        if h_pivs["Ready"]:
            output["max-pivots-ready-for-entry"].append({"Stock": s.ticker, "Data": h_pivs["Ready"]})
        if l_pivs["Ready"]:
            output["min-pivots-ready-for-entry"].append({"Stock": s.ticker, "Data": l_pivs["Ready"]})

        # 4. Moving Averages (Matches JS: if (Array.isArray(s) && s.length === 2))
        ma_list = logic.get_ma_distance_logic(s)
        for ma in ma_list:
            key = f"close-to-{ma['window']}-{'3-atr' if ma['ATR_Match'] else 'slow-atr'}"
            if key in output:
                # Pack as [Ticker, Label] so the JS pill shows the yellow subtext
                output[key].append([s.ticker, "Above" if ma["Above"] else "Below"])

        # 5. SMA 20 Distance
        f20 = logic.get_far_from_20_logic(s)
        if f20:
            key = f"{f20[1].lower()}-from-20-above-2x-atr"
            if key in output:
                output[key].append([s.ticker, f20[1]]) # f20[1] is "ABOVE" or "BELOW"

    return database.save_results(output)



def load_local_model():
    """Loads the model from the local disk into RAM using absolute paths."""
    #  Get the absolute path of Scraper.py
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    project_root = os.path.join(current_dir, "..", "..")
    file_path = os.path.join(project_root, "trading_model.joblib")
    
    #  Normalize the path (fixes slash issues between Windows/Linux)
    file_path = os.path.abspath(file_path)

    if os.path.exists(file_path):
        data = joblib.load(file_path)
        print(f"✅ Local brain loaded from: {file_path}")
        print(f"✅ Accuracy: {data['accuracy']:.2f}")
        return data['model'], data['features']
    else:
        print(f"❌ No local model file found at: {file_path}")
        print("💡 Check if the file is in the root directory and included in your Git commit.")
        return None, None



    """Fetches stats from Realtime Database."""
    return db.reference("model_stats").get()

def apply_indicators(df):
    """
    Calculates the features required for the new high-accuracy ML model layout.
    """
    # 1. Ironclad Column Flattening
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).strip() for col in df.columns]

    # Ensure download was successful
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required):
        return None

    # 2. EXTRAW RAW SERIES
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    vol = df['Volume'].squeeze()
    
    # 3. BASE CALCS
    atr = ta.atr(high, low, close, 14) + 0.0001
    sma20 = ta.sma(close, 20)
    sma100 = ta.sma(close, 100)
    
    # 4. TARGET LOGIC (5-Day Mean Reversion to SMA20)
    df['Target'] = 0
    for i in range(len(df) - 5):
        future_highs = high.iloc[i+1 : i+6]
        future_smas = sma20.iloc[i+1 : i+6]
        if (future_highs >= future_smas).any():
            df.at[df.index[i], 'Target'] = 1

    # 5. NEW HIGH-ACCURACY FEATURE ENGINEERING
    df['stretch_sma20'] = (sma20 - close) / atr
    df['stretch_sma100'] = (sma100 - close) / atr

    # Oscillators (RSI Slope 3)
    rsi_14 = ta.rsi(close, 14) / 100.0
    df['rsi_slope_3'] = rsi_14.diff(3)

    # Volatility Structures (BB %B)
    bb20 = ta.bbands(close, length=20)
    if bb20 is not None:
        df['bb_pct_b'] = (close - bb20.iloc[:, 0]) / (bb20.iloc[:, 2] - bb20.iloc[:, 0] + 0.0001)
    else:
        df['bb_pct_b'] = 0.5
    
    # Momentum Vectors
    df['roc_5'] = close.pct_change(5)
    df['roc_10'] = close.pct_change(10)
    df['roc_20'] = close.pct_change(20)

    # Rolling Extremes Multi-Period Distances
    df['dist_from_high_20'] = (high.rolling(20).max() - close) / atr

    # Volume Profiling
    df['volume_ratio_5'] = vol / (ta.sma(vol, 5) + 0.0001)
    df['cmf_20'] = ta.cmf(high, low, close, vol, length=20).fillna(0)

    # 6. FILTER: ONLY TEACH THE MODEL ABOUT "STRETCHED" DAYS
    df['stretch_filter'] = (sma20 - close) / atr
    df = df[df['stretch_filter'] > 0.5].drop(columns=['stretch_filter']).copy()

    # 7. SELECT FINAL FEATURE COLUMNS (The Top 10 Best Accuracy List)
    features = [
        'stretch_sma20', 'roc_5', 'roc_10', 'roc_20', 'bb_pct_b', 
        'volume_ratio_5', 'cmf_20', 'rsi_slope_3', 'stretch_sma100', 'dist_from_high_20'
    ]
    
    return df[features + ['Target']].dropna()

def scan_stock(ticker, model, feature_cols):
    """Single stock prediction using local model."""
    df = yf.download(ticker, period="200d", progress=False)
    
    if df.empty:
        return None
        
    # 1. Flatten yfinance MultiIndex headers immediately if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).strip() for col in df.columns]
    
    # 2. CRITICAL CHANGE: Use the exact training feature engine instead of apply_indicators
    # This guarantees 'stretch_sma20', 'roc_5', etc., actually get calculated!
    df = apply_indicators(df)
    
    if df is None or df.empty:
        return None
        
    # 3. Clean headers again post-calculation to ensure perfect matching
    df.columns = [str(col).strip() for col in df.columns]
    
    try:
        # Extract only the 10 top accuracy features loaded from your joblib payload
        current_setup = df[feature_cols].tail(1)
    except KeyError as e:
        print(f"💥 Missing expected ML feature in live data for {ticker}: {e}")
        return None
    
    if current_setup.isnull().values.any(): 
        return None
        
    model_Prob_Result = model.predict_proba(current_setup)[0][1]
    database.upload_ML_Prob_To_Firebase(GlobalUserName_Var, ticker, model_Prob_Result)
    return model_Prob_Result



features = ['stretch', 'ATR', 'SMA50_STRETCH', 'SMA150_STRETCH', 'RSI', 'volume_ratio', 'OBV', 'ROC', 
            'BB_Width', 'Closed_At_Range', 'RSI_Slope', 'CCI', 'Dist_From_Low', 'ATR_Ratio', 'Vol_Shock', 'Price_Speed']

# --- EXECUTION ---
# Change to "TRAIN" once, then "SCAN" forever after.

#THIS IS GOING TO BE TRAIN ONLY ON MY LOCAL MACHINE,SO I CAN TRAIN IT THEN REUPLOAD THE TRAINED MODEL TO THE GITHUB
MODE = "SCAN" 

if MODE == "TRAIN":
    tickers = commaSeparatedInputToListOfTickers() # Your list
    active_model = train_and_save_locally(tickers)


    

#this assumes theres already a model trained and saved locally, if not it will throw an error, but you can change the code to train if no model is found
def Scan_Tickers(list_tickers):
    results=[]
    active_model, active_features = load_local_model()
    if active_model:
        for ticker in list_tickers:
            prob = scan_stock(ticker, active_model, active_features)
            results.append((ticker, prob))
    return results

def commaSeparatedInputToListOfTickers():
    input_string = input("Enter stock tickers separated by commas: ")
    tickers = [ticker.strip().upper() for ticker in input_string.split(",")]
    return tickers


def train_and_save_locally(ticker_list):
    """Downloads data, applies indicators, trains RF, and saves to disk."""
    master_data = []
    
    print(f"--- Starting Education Phase with {len(ticker_list)} tickers ---")
    
    for ticker in ticker_list:
        try:
            # Download 3y to have enough history for SMAs
            df = yf.download(ticker, period='3y', progress=False)
            if df.empty: continue
            
            processed_df = apply_indicators(df)
            
            if processed_df is not None and not processed_df.empty:
                master_data.append(processed_df)
                print(f"✅ {ticker}: Processed {len(processed_df)} setups.")
            
            gc.collect() # Reset RAM after each ticker
        except Exception as e:
            print(f"❌ {ticker}: Failed due to {e}")

    if not master_data:
        return print("Error: No data was collected. Check your ticker list.")

    # Merge all tickers into one massive training table
    full_df = pd.concat(master_data)
    
    # Define X (features) and y (target)
    feature_cols = [c for c in full_df.columns if c != 'Target']
    X = full_df[feature_cols]
    y = full_df['Target']

    # SPLIT DATA: Train on 80%, Test on 20% (Prevents 100% fake accuracy)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\nTraining on {len(X_train)} samples...")
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    # Validate
    accuracy = model.score(X_test, y_test)
    print(f"--- TRAINING COMPLETE ---")
    print(f"Real-World Accuracy: {accuracy*100:.2f}%")
    
    # Save everything into one local file
    model_payload = {
        'model': model,
        'features': feature_cols,
        'accuracy': accuracy
    }
    joblib.dump(model_payload, 'trading_model.joblib')
    print("📁 Model saved locally as 'trading_model.joblib'")
    
    return model


