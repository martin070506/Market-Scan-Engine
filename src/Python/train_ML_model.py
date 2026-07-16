import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import gc
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# --- 1. USER CONFIGURATION ---
def commaSeparatedInputToListOfTickers():
    input_string = input("Enter stock tickers separated by commas: ")
    tickers = [ticker.strip().upper() for ticker in input_string.split(",")]
    return tickers
TICKERS_POOL = commaSeparatedInputToListOfTickers()

MODEL_FILENAME = "trading_model.joblib"

# --- TOP 10 HIGHEST ACCURACY FEATURES FOR ML TRAINING ---
BEST_ACCURACY_FEATURES = [
    'stretch_sma20',
    'roc_5',
    'roc_10',
    'roc_20',
    'bb_pct_b',
    'volume_ratio_5',
    'cmf_20',
    'rsi_slope_3',
    'stretch_sma100',
    'dist_from_high_20'
]


# --- 2. THE ENGINEERING PIPELINE ---
def generate_all_normalized_features(df):
    """
    Calculates all background features to preserve full matrix logic.
    """
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required):
        return None

    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    open_p = df['Open'].squeeze()
    vol = df['Volume'].squeeze()
    
    atr = ta.atr(high, low, close, 14) + 0.0001
    sma20 = ta.sma(close, 20)
    # sma50 = ta.sma(close, 50)
    sma100 = ta.sma(close, 100)
    # sma200 = ta.sma(close, 200)
    
    features_df = pd.DataFrame(index=df.index)
    
    # Target Logic: Mean Reversion to SMA20 within 5 days
    features_df['Target'] = 0
    for i in range(len(df) - 5):
        future_highs = high.iloc[i+1 : i+6]
        future_smas = sma20.iloc[i+1 : i+6]
        if (future_highs >= future_smas).any():
            features_df.at[df.index[i], 'Target'] = 1

    # COMMENTED OUT NON NEEDED FAETURES, IF THEYRE NEEDED, UNCOMMENT THEM AND ADD TO BEST_ACCURACY_FEATURES LIST

    # Moving Average Stretch (Normalized by ATR)
    features_df['stretch_sma20'] = (sma20 - close) / atr
    # features_df['stretch_sma50'] = (sma50 - close) / atr
    features_df['stretch_sma100'] = (sma100 - close) / atr
    # features_df['stretch_sma200'] = (sma200 - close) / atr
    # features_df['sma20_vs_sma50'] = (sma20 - sma50) / atr
    # features_df['sma50_vs_sma200'] = (sma50 - sma200) / atr

    # Oscillators
    # features_df['rsi_14'] = ta.rsi(close, 14) / 100.0
    # features_df['rsi_7'] = ta.rsi(close, 7) / 100.0
    # features_df['rsi_28'] = ta.rsi(close, 28) / 100.0
    features_df['rsi_slope_3'] = (ta.rsi(close, 14) / 100.0).diff(3)
    # features_df['rsi_slope_5'] = features_df['rsi_14'].diff(5)
    # features_df['cci_14'] = ta.cci(high, low, close, 14) / 100.0
    # features_df['cci_20'] = ta.cci(high, low, close, 20) / 100.0
    # features_df['willr_14'] = ta.willr(high, low, close, 14) / -100.0
    
    # stoch = ta.stoch(high, low, close)
    # features_df['stoch_k'] = stoch.iloc[:, 0] / 100.0 if stoch is not None else 0.5
    # features_df['stoch_d'] = stoch.iloc[:, 1] / 100.0 if stoch is not None else 0.5

    # Candlestick Mechanics
    # features_df['closed_at_range'] = (close - low) / (high - low + 0.0001)
    # features_df['open_at_range'] = (open_p - low) / (high - low + 0.0001)
    # features_df['body_to_range'] = (close - open_p).abs() / (high - low + 0.0001)
    # features_df['upper_shadow_ratio'] = (high - np.maximum(open_p, close)) / (high - low + 0.0001)
    # features_df['lower_shadow_ratio'] = (np.minimum(open_p, close) - low) / (high - low + 0.0001)

    # Volatility Structures
    # features_df['atr_ratio'] = atr / (ta.sma(atr, 20) + 0.0001)
    # features_df['atr_pct_of_price'] = atr / close
    
    bb20 = ta.bbands(close, length=20)
    if bb20 is not None:
        # features_df['bb_width_20'] = (bb20.iloc[:, 2] - bb20.iloc[:, 0]) / (sma20 + 0.0001)
        features_df['bb_pct_b'] = (close - bb20.iloc[:, 0]) / (bb20.iloc[:, 2] - bb20.iloc[:, 0] + 0.0001)
    
    # kc = ta.kc(high, low, close, length=20)
    # if kc is not None:
    #     features_df['kc_width'] = (kc.iloc[:, 2] - kc.iloc[:, 0]) / (sma20 + 0.0001)

    # Momentum Vectors
    # features_df['roc_1'] = close.pct_change(1)
    # features_df['roc_3'] = close.pct_change(3)
    features_df['roc_5'] = close.pct_change(5)
    features_df['roc_10'] = close.pct_change(10)
    features_df['roc_20'] = close.pct_change(20)
    # features_df['price_speed_3'] = features_df['roc_5'].diff(3)
    # features_df['price_acceleration'] = features_df['price_speed_3'].diff(2)

    # Rolling Extremes Multi-Period Distances
    # for p in [3, 5, 10, 20]:
    #     features_df[f'dist_from_low_{p}'] = (close - low.rolling(p).min()) / atr
    #     features_df[f'dist_from_high_{p}'] = (high.rolling(p).max() - close) / atr
    features_df['dist_from_high_20'] = (high.rolling(20).max() - close) / atr

    # Volume Profiling
    # vol_sma20 = ta.sma(vol, 20) + 0.0001
    # features_df['volume_ratio_20'] = vol / vol_sma20
    features_df['volume_ratio_5'] = vol / (ta.sma(vol, 5) + 0.0001)
    # features_df['vol_shock_std'] = (vol - vol_sma20) / (ta.stdev(vol, 20) + 0.0001)
    # features_df['obv_slope'] = ta.obv(close, vol).pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
    # features_df['pvt_norm'] = ta.pvt(close, vol).pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
    features_df['cmf_20'] = ta.cmf(high, low, close, vol, length=20).fillna(0)
    # features_df['mfi_14'] = ta.mfi(high, low, close, vol, length=14).fillna(0) / 100.0

    # STRETCH FILTER (Matches Scanner Logic)
    features_df['stretch_filter'] = (sma20 - close) / atr
    features_df = features_df[features_df['stretch_filter'] > 0.5].drop(columns=['stretch_filter'])

    return features_df


def run_training_pipeline():
    master_data = []
    print(f"🚀 Starting Engine Training Phase using {len(TICKERS_POOL)} assets...")

    for ticker in TICKERS_POOL:
        try:
            df = yf.download(ticker, period='3y', progress=False)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(col).strip() for col in df.columns]

            processed_df = generate_all_normalized_features(df)
            if processed_df is not None and not processed_df.empty:
                master_data.append(processed_df)
                print(f"  📊 {ticker}: Extracted {len(processed_df)} structural setups.")
            
            gc.collect()
        except Exception as e:
            print(f"  ❌ {ticker}: Processing failure -> {e}")

    if not master_data:
        print("💥 Error: No training matrix was built.")
        return

    full_df = pd.concat(master_data, axis=0).dropna()
    
    # --- FILTERING ONLY THE BEST ACCURACY FEATURES FOR RANDOM FOREST ---
    try:
        X = full_df[BEST_ACCURACY_FEATURES]
        y = full_df['Target']
    except KeyError as e:
        print(f"💥 Error: One of your core accurate features was missing from calculations: {e}")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\n⚙️ Training Random Forest Classifier on {len(X_train)} samples using top 10 features...")

    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f"\n📈 Real-World Out-of-Sample Accuracy: {accuracy*100:.2f}%")

    model_payload = {
        'model': model,
        'features': BEST_ACCURACY_FEATURES,
        'accuracy': accuracy
    }
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..")
        file_path = os.path.join(project_root, MODEL_FILENAME)
    except NameError:
        file_path = MODEL_FILENAME
        
    file_path = os.path.abspath(file_path)

    joblib.dump(model_payload, file_path)
    print(f"⚠️  SUCCESS: Overwrote local file '{file_path}' with optimal feature layout.")


if __name__ == "__main__":
    run_training_pipeline()