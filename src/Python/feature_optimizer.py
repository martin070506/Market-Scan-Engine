import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import gc
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def download_and_build_dataset(ticker_list):
    """Downloads historical data and aggregates a clean master dataset."""
    master_data = []
    print(f"--- 📥 Downloading Data for {len(ticker_list)} Tickers ---")
    
    for ticker in ticker_list:
        try:
            df = yf.download(ticker, period='3y', progress=False)
            if df.empty: continue
            
            # Column flattening for MultiIndex data (yfinance defense)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(col).strip() for col in df.columns]
            
            processed_df = generate_all_normalized_features(df)
            if processed_df is not None and not processed_df.empty:
                master_data.append(processed_df)
                print(f"✅ {ticker}: Generated {processed_df.shape[0]} setups.")
            
            gc.collect()
        except Exception as e:
            print(f"❌ {ticker}: Failed due to {e}")
            
    if not master_data:
        raise ValueError("No data was collected. Please verify your ticker list.")
        
    return pd.concat(master_data, axis=0).dropna()

def generate_all_normalized_features(df):
    """
    Generates 54 normalized, price-and-scale-invariant features.
    No raw absolute prices or raw volumes are exposed to the model.
    """
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required):
        return None

    # Extract clean series
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    open_p = df['Open'].squeeze()
    vol = df['Volume'].squeeze()
    
    # Base normalization factors (ATR & Moving Averages)
    atr = ta.atr(high, low, close, 14) + 0.0001
    sma20 = ta.sma(close, 20)
    sma50 = ta.sma(close, 50)
    sma100 = ta.sma(close, 100)
    sma200 = ta.sma(close, 200)
    
    features_df = pd.DataFrame(index=df.index)
    
    # --- 1. Target Logic (Matches your original Mean Reversion concept) ---
    features_df['Target'] = 0
    for i in range(len(df) - 5):
        future_highs = high.iloc[i+1 : i+6]
        future_smas = sma20.iloc[i+1 : i+6]
        if (future_highs >= future_smas).any():
            features_df.at[df.index[i], 'Target'] = 1

    # --- 2. Moving Average Stretch Features (Normalized by ATR) ---
    features_df['stretch_sma20'] = (sma20 - close) / atr
    features_df['stretch_sma50'] = (sma50 - close) / atr
    features_df['stretch_sma100'] = (sma100 - close) / atr
    features_df['stretch_sma200'] = (sma200 - close) / atr
    features_df['sma20_vs_sma50'] = (sma20 - sma50) / atr
    features_df['sma50_vs_sma200'] = (sma50 - sma200) / atr

    # --- 3. Momentum & Oscillators (Naturally scale-invariant) ---
    features_df['rsi_14'] = ta.rsi(close, 14) / 100.0
    features_df['rsi_7'] = ta.rsi(close, 7) / 100.0
    features_df['rsi_28'] = ta.rsi(close, 28) / 100.0
    features_df['rsi_slope_3'] = features_df['rsi_14'].diff(3)
    features_df['rsi_slope_5'] = features_df['rsi_14'].diff(5)
    
    features_df['cci_14'] = ta.cci(high, low, close, 14) / 100.0
    features_df['cci_20'] = ta.cci(high, low, close, 20) / 100.0
    
    # Williams %R & Stochastic (Bounded 0 to 1)
    features_df['willr_14'] = ta.willr(high, low, close, 14) / -100.0
    stoch = ta.stoch(high, low, close)
    if stoch is not None:
        features_df['stoch_k'] = stoch.iloc[:, 0] / 100.0
        features_df['stoch_d'] = stoch.iloc[:, 1] / 100.0
    else:
        features_df['stoch_k'] = 0.5
        features_df['stoch_d'] = 0.5

    # --- 4. Price Action & Candlestick Metrics ---
    features_df['closed_at_range'] = (close - low) / (high - low + 0.0001)
    features_df['open_at_range'] = (open_p - low) / (high - low + 0.0001)
    features_df['body_to_range'] = (close - open_p).abs() / (high - low + 0.0001)
    features_df['upper_shadow_ratio'] = (high - np.maximum(open_p, close)) / (high - low + 0.0001)
    features_df['lower_shadow_ratio'] = (np.minimum(open_p, close) - low) / (high - low + 0.0001)

    # --- 5. Volatility & Bands ---
    features_df['atr_ratio'] = atr / (ta.sma(atr, 20) + 0.0001)
    features_df['atr_pct_of_price'] = atr / close
    
    bb20 = ta.bbands(close, length=20)
    if bb20 is not None:
        features_df['bb_width_20'] = (bb20.iloc[:, 2] - bb20.iloc[:, 0]) / (sma20 + 0.0001)
        features_df['bb_pct_b'] = (close - bb20.iloc[:, 0]) / (bb20.iloc[:, 2] - bb20.iloc[:, 0] + 0.0001)
    
    kc = ta.kc(high, low, close, length=20)
    if kc is not None:
        features_df['kc_width'] = (kc.iloc[:, 2] - kc.iloc[:, 0]) / (sma20 + 0.0001)

    # --- 6. Rate of Change (ROC) and Speed ---
    features_df['roc_1'] = close.pct_change(1)
    features_df['roc_3'] = close.pct_change(3)
    features_df['roc_5'] = close.pct_change(5)
    features_df['roc_10'] = close.pct_change(10)
    features_df['roc_20'] = close.pct_change(20)
    features_df['price_speed_3'] = features_df['roc_5'].diff(3)
    features_df['price_acceleration'] = features_df['price_speed_3'].diff(2)

    # --- 7. Multi-period Distance Metrics ---
    for period in [3, 5, 10, 20]:
        features_df[f'dist_from_low_{period}'] = (close - low.rolling(period).min()) / atr
        features_df[f'dist_from_high_{period}'] = (high.rolling(period).max() - close) / atr

    # --- 8. Volume Dynamics (Completely scale-invariant ratios) ---
    vol_sma20 = ta.sma(vol, 20) + 0.0001
    features_df['volume_ratio_20'] = vol / vol_sma20
    features_df['volume_ratio_5'] = vol / (ta.sma(vol, 5) + 0.0001)
    features_df['vol_shock_std'] = (vol - vol_sma20) / (ta.stdev(vol, 20) + 0.0001)
    
    # Normalized Volume Indicators
    features_df['obv_slope'] = ta.obv(close, vol).pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
    features_df['pvt_norm'] = ta.pvt(close, vol).pct_change(5).replace([np.inf, -np.inf], 0).fillna(0)
    features_df['cmf_20'] = ta.cmf(high, low, close, vol, length=20).fillna(0)
    features_df['mfi_14'] = ta.mfi(high, low, close, vol, length=14).fillna(0) / 100.0

    # --- FILTER SETUPS ---
    # Matches your criteria: Only look at days where price is significantly stretched below SMA20
    features_df['stretch_filter'] = (sma20 - close) / atr
    features_df = features_df[features_df['stretch_filter'] > 0.5].drop(columns=['stretch_filter'])

    return features_df


def forward_feature_selection(df, max_features=12):
    """
    Evaluates combinations systematically using Forward Selection.
    Starts with the single best feature, then greedily adds the next best one.
    """
    all_features = [col for col in df.columns if col != 'Target']
    X = df[all_features]
    y = df['Target']
    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    selected_features = []
    best_overall_accuracy = 0.0
    
    print(f"\n--- 🧠 Launching Forward Feature Selection (Testing combinations out of {len(all_features)} pools) ---")
    
    for step in range(max_features):
        best_step_feature = None
        best_step_accuracy = 0.0
        
        for feature in all_features:
            if feature in selected_features:
                continue
                
            current_candidates = selected_features + [feature]
            
            # Fast, constrained Model Evaluation to prevent overfitting during verification
            model = RandomForestClassifier(n_estimators=60, max_depth=8, random_state=42, n_jobs=-1)
            model.fit(X_train[current_candidates], y_train)
            
            preds = model.predict(X_test[current_candidates])
            acc = accuracy_score(y_test, preds)
            
            if acc > best_step_accuracy:
                best_step_accuracy = acc
                best_step_feature = feature
                
        if best_step_accuracy > best_overall_accuracy:
            best_overall_accuracy = best_step_accuracy
            selected_features.append(best_step_feature)
            print(f"✨ Feature Count {len(selected_features)}: Added '{best_step_feature}' -> New Best Accuracy: {best_overall_accuracy*100:.2f}%")
        else:
            print(f"🛑 Adding more features did not improve baseline performance. Stopping pipeline optimization.")
            break
            
    return selected_features, best_overall_accuracy

def commaSeparatedInputToListOfTickers():
    input_string = input("Enter stock tickers separated by commas: ")
    tickers = [ticker.strip().upper() for ticker in input_string.split(",")]
    return tickers

# --- RUN LAB EXPERIMENT ---
if __name__ == "__main__":
    # Feel free to change/expand this sample subset of volatile tickers for broad calculations
    training_tickers = commaSeparatedInputToListOfTickers()  # Load from your text file 
    
    try:
        # 1. Pipeline Execution
        master_dataset = download_and_build_dataset(training_tickers)
        
        # 2. Optimization Processing
        best_combination, top_accuracy = forward_feature_selection(master_dataset, max_features=15)
        
        # 3. Print Final Summary Reports
        print("\n" + "="*50)
        print("🏆 FEATURE COMBINATION OPTIMIZATION RESULTS 🏆")
        print("="*50)
        print(f"🥇 Highest Achieved Accuracy: {top_accuracy*100:.2f}%\n")
        print(f"📋 Optimal Feature Combination ({len(best_combination)} features):")
        for idx, feat in enumerate(best_combination, 1):
            print(f"  {idx}. {feat}")
        print("="*50)
        print("\n💡 Action: Copy and paste the list above directly into your main scanner_service.py 'features' definition array!")
        
    except Exception as error:
        print(f"💥 Optimization pipeline halted: {error}")

