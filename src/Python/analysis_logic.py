import pandas as pd
import numpy as np

class CupHandleValidator:
    MIN_PIVOT_GAP = 20
    MIN_TOTAL_DURATION = 65

    @staticmethod
    def check_cup_handle(stock, pivots_from_method):
        all_points = sorted([p for group in pivots_from_method for p in group], key=lambda x: x[2])
        if len(all_points) < 3: return {"Bool": False}

        for i in range(len(all_points) - 2):
            p1 = all_points[i]
            for j in range(i + 1, len(all_points) - 1):
                p2 = all_points[j]
                # ... (Keep your gap and resistance checks)
                for k in range(j + 1, len(all_points)):
                    p3 = all_points[k]
                    
                    # Horizontal Resistance check (same as your original)
                    avg = (p1[0] + p2[0] + p3[0]) / 3
                    if all(0.985 * avg <= p <= 1.015 * avg for p in [p1[0], p2[0], p3[0]]):
                        
                        # Validate structure/handle...
                        # If valid, return the dates of these three pivots:
                        
                            return {
                                "Bool": True, 
                                "Dates": [p1[1], p2[1], p3[1]] # <--- Return the 3 pivot dates
                            }
        return {"Bool": False}

# analysis_logic.py

def find_pivots(series, is_high=True):
    if series is None or series.empty: return {"Ready": [], "NotReady": []}
    pivots, n, ignore = [], len(series), set()
    
    for i in range(n):
        if i in ignore: continue
        price, date, zone = series.iloc[i], series.index[i], []
        # JS expects: [price, date_string, bar_index]
        zone.append([float(price), date.strftime('%Y-%m-%d'), int(i)])
        
        j, ceiling, floor = i + 6, price * 1.013, price * 0.987
        while j < n:
            curr = series.iloc[j]
            if is_high and curr > ceiling: break
            if not is_high and curr < floor: break
            if floor <= curr <= ceiling:
                zone.append([float(curr), series.index[j].strftime('%Y-%m-%d'), int(j)])
                j += 20
            j += 1
            
        if len(zone) >= 3:
            pivots.append(zone)
            ignore.update([p[2] for p in zone])
            
    # Logic for Ready/NotReady remains same
    ready, not_ready = [], []
    curr_p = series.iloc[-1]
    for p in pivots:
        orig_price = p[0][0]
        subset = series.iloc[p[0][2]:]
        if is_high:
            if (subset <= 1.03 * orig_price).all():
                if curr_p >= 0.97 * orig_price: ready.append(p)
                elif curr_p >= 0.90 * orig_price: not_ready.append(p)
        else:
            if (subset >= 0.97 * orig_price).all():
                if curr_p <= 1.03 * orig_price: ready.append(p)
                else: not_ready.append(p)
    return {"Ready": ready, "NotReady": not_ready}

def get_ma_distance_logic(stock):
    results = []
    prices = stock.close_prices_1y
    for window in [150, 200]:
        if len(prices) < window: continue
        sma = prices.rolling(window=window).mean().iloc[-1]
        curr = prices.iloc[-1]
        if sma * 0.97 <= curr <= sma * 1.03:
            atr_match = (stock.atr >= 3.0)
            results.append({"window": window, "Ticker": stock.ticker, "ATR_Match": atr_match,"Above": curr > sma})
    return results

def get_far_from_20_logic(stock):
    prices = stock.close_prices_1y
    if len(prices) < 20: return None
    sma20 = prices.rolling(window=20).mean().iloc[-1]
    curr = prices.iloc[-1]
    if stock.atr > (2 * 1.5): # Assuming 1.5 as base or similar to your 2x ATR logic
        if curr > sma20 * 1.10: return (stock.ticker, "ABOVE")
        if curr < sma20 * 0.90: return (stock.ticker, "BELOW")
    return None