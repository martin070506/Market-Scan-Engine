import uuid
from fastapi import FastAPI, UploadFile, File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import numpy as np
from dataclasses import dataclass
import math
app = FastAPI()

@dataclass
class StockInfo:
    ticker: str
    atr: int =0
    high_prices_3y: pd.Series = None
    close_prices_1y: pd.Series = None
    low_prices_1y: pd.Series = None
    

    def download_all_data(self):
        """Downloads and prepares the Series with Dates as the Index."""
        data = yf.download(self.ticker, period="3y", auto_adjust=True, progress=False)
        
        if data.empty:
            return

        # Clean Multi-Index columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # We keep these as Pandas Series because they contain the .index (Dates)
        self.high_prices_3y = data['High']
        self.close_prices_1y = data['Close'].tail(365)
        self.low_prices_1y = data['Low'].tail(365)
        self.calc_atr()


    def calc_atr(self):
        """
        Downloads 15 days of data for a specific ticker string 
        and returns the ATR as a percentage of the current price.
        Includes safety checks for JSON-compliant return values.
        """
        ticker_str=self.ticker
        try:
            data = yf.download(ticker_str, period="15d", auto_adjust=True, progress=False)
            
            if data.empty or len(data) < 15:
               self.atr= 0.0

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            close = data['Close']
            high  = data['High']
            low   = data['Low']

            tr0 = high - low
            tr1 = (high - close.shift(1)).abs()
            tr2 = (low  - close.shift(1)).abs()
            tr  = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)
            n = 14
            atr14_initial = tr.iloc[1:15].dropna().mean()
            
            last_tr = tr.iloc[-1]
            atr_latest = ((atr14_initial * (n - 1)) + last_tr) / n

            current_price = close.iloc[-1]
            
            if current_price == 0 or np.isnan(current_price):
                self.atr=0

            atr_percent = (atr_latest / current_price) * 100.0

            if np.isnan(atr_percent) or np.isinf(atr_percent):
                self.atr= 0.0
            print(f"ATR Calculation Success for {ticker_str}: {atr_percent}")
            self.atr= float(atr_percent)

        except Exception as e:
            print(f"ATR Calculation Error for {ticker_str}: {e}")
            self.atr= 0.0



# ✅ allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "https://mar-stocks.netlify.app","http://127.0.0.1:5500","http://127.0.0.1:8000","http://localhost:8000"],
    allow_credentials=False,   # set True only if you use cookies/sessions
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- CSV validation ----------
def check_Correct_Format_CSV(f):
    try:
        df = pd.read_csv(f)
    except Exception as e:
        return False, f"Failed to read CSV: {e}"
    if len(df.columns) == 0:
        return False, "CSV has no columns."
    first_col = df.columns[0]
    if first_col != "Ticker":
        return False, f"First column must be 'Ticker', got '{first_col}'."
    return True, None

class RequestData(BaseModel):
    text: str



@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        return {"success": False, "error": f"File must be a CSV. Got: '{file.filename}'"}

    is_valid, error = check_Correct_Format_CSV(file.file)
    if not is_valid:
        return {"success": False, "error": error}

    return {"success": True, "message": "CSV format is correct (first column is 'Ticker')."}



def clean_json_data(obj):
    """Recursively replaces NaN/Inf with 0 so JSON doesn't crash."""
    if isinstance(obj, list):
        return [clean_json_data(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj



results_cache={}
@app.post("/run_logic")
async def Run_Entire_Script(file: UploadFile=File(...)):

    listOfStocks =fromCSV_to_listOfStocks(file.file)
    TotalList=Cup_Handle_Stocks_And_Pivot_Stocks(listOfStocks)
    Cup_Handle=TotalList["Cup And Handle"]
    Support=TotalList["Support"]
    Resistance=TotalList["Resistance"]
    List_Double_Bottom_Stocks=Double_Bottom_Stocks(listOfStocks)
    List_Close_to_avg_Stocks=Close_to_avg_Stocks(listOfStocks)
    
    """HERE WE JUST USE THE FUNCTIONS WE ALREADY MADE
    we also filter here for above atr stocks and stuff like that
    """
    Close_150_Slow_ATR=[(Res["Ticker"],Res["Status"]) for Res in List_Close_to_avg_Stocks[0] if not Res["ATR_Match"]]
    Close_200_Slow_ATR=[(Res["Ticker"],Res["Status"]) for Res in List_Close_to_avg_Stocks[1] if not Res["ATR_Match"]]
    Close_150_3_ATR=[(Res["Ticker"],Res["Status"]) for Res in List_Close_to_avg_Stocks[0] if  Res["ATR_Match"]]
    Close_200_3_ATR=[(Res["Ticker"],Res["Status"]) for Res in List_Close_to_avg_Stocks[1] if  Res["ATR_Match"]]
    #THESE ARE STRINGS, SO TO CALCULATE ATR WE NEED TO DOWNLAD 15D OF DATA AGAIN

    farFrom20=Far_From_20_Stocks(listOfStocks)
    #HERE GET ATRT GETS A STRING SO WE DOWNLOAD MORE DATA
    
    Above_20_And_ATR_Match=[pair[0] for pair in farFrom20 if pair[1]=='ABOVE' ]
    Below_20_And_ATR_Match=[pair[0] for pair in farFrom20 if pair[1]=='BELOW']
    
    

    result_id=str(uuid.uuid4())
    raw_results={
        "cup_handle": Cup_Handle,
        "double_bottom": List_Double_Bottom_Stocks,
        "close_to_150_slow_atr":Close_150_Slow_ATR,
        "close_to_200_slow_atr":Close_200_Slow_ATR,
        "close_to_150_3_atr":Close_150_3_ATR,
        "close_to_200_3_atr":Close_200_3_ATR,
        "above_from_20_and_above_2x_atr":Above_20_And_ATR_Match,
        "below_from_20_and_above_2x_atr":Below_20_And_ATR_Match,
        "min_pivots_ready_for_entry": Support,
        "max_pivots_ready_for_entry": Resistance
        }
    results_cache[result_id]=clean_json_data(raw_results)
    return {"success": True, "result_id": result_id}


@app.get("/results/{result_id}/cup-handle")
async def get_cup_handle(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["cup_handle"]}

@app.get("/results/{result_id}/double-bottom")
async def get_double_bottom(result_id: str):
    if result_id not in results_cache:
        raise  HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["double_bottom"]}




@app.get("/results/{result_id}/close-to-150-slow-atr")
async def get_close_to_150_slow_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_150_slow_atr"]}

@app.get("/results/{result_id}/close-to-150-3-atr")
async def get_close_to_150_3_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_150_3_atr"]}
            
@app.get("/results/{result_id}/close-to-200-slow-atr")
async def get_close_to_200_slow_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_200_slow_atr"]}

@app.get("/results/{result_id}/close-to-200-3-atr")
async def get_close_to_200_3_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_200_3_atr"]}

@app.get("/results/{result_id}/above-from-20-above-2x-atr")
async def get_above_from_20_above_2x_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["above_from_20_and_above_2x_atr"]}

@app.get("/results/{result_id}/below-from-20-above-2x-atr")
async def get_below_from_20_above_2x_atr(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["below_from_20_and_above_2x_atr"]}


@app.get("/results/{result_id}/close-to-150-and-3-atr")
async def get_close_to_150_atr_3(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_150_and_3_atr"]}

#this specific thing is hardcoded but the functions are generic (user input) so the website will have it 



@app.get("/results/{result_id}/min-pivots-ready-for-entry")
async def get_min_pivots_ready_for_entry(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["min_pivots_ready_for_entry"]}

@app.get("/results/{result_id}/max-pivots-ready-for-entry")
async def get_max_pivots_ready_for_entry(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["max_pivots_ready_for_entry"]}







def fromCSV_to_listOfStocks(file):
   
    file.seek(0) 
    df = pd.read_csv(file)
    listOfTickers = df['Ticker'].dropna().unique().tolist()
    listOfStockInfo = []
    for val in listOfTickers:
        s = StockInfo(ticker=str(val).strip().upper())
        s.download_all_data()
        if s.close_prices_1y is not None:
            listOfStockInfo.append(s)
    return listOfStockInfo








def Double_Bottom_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT HAVE DOUBLE BOTTOM PATTERN
    return []


def IsStock_Double_Bottom(stock):
    #GETS A STOCK TICKER(string) AND RETURNS TRUE IF IT HAS DOUBLE BOTTOM PATTERN
    pass











#------------------------------------------------------------ general things, like pivots , max/min in a span 





    
     



def findHighPivots(stock: StockInfo):
    """
    Finds pivot points where the price stays within a 1.3% ceiling
    using the StockInfo object data.
    """
    # 1. Access data from the class
    HighPrices = stock.high_prices_3y
    
    if HighPrices is None or HighPrices.empty:
        return {"Ready": [], "NotReady": []}

    pivotsHigh = []
    n = len(HighPrices)
    indexToIgnore = set()  # Using a set for faster 'in' checks

    # Main Logic Loop
    for i in range(n):
        if i in indexToIgnore:
            continue
            
        # Get price and date from the Series
        originalPricePoint = HighPrices.iloc[i]
        originalDatePoint = HighPrices.index[i]
        
        # Math: 1.3% Buffer
        upper_limit = 1.013 * originalPricePoint
        lower_limit = 0.987 * originalPricePoint
        
        tempResult = []
        # Store as (Price, DateString, Index)
        tempResult.append((originalPricePoint, originalDatePoint.strftime('%Y-%m-%d'), i))
        
        j = i + 6 
        tempIndexes = [i]
        
        while j < n:
            if j in indexToIgnore:
                j += 1
                continue
            
            currentPrice = HighPrices.iloc[j]
            
            # If price breaks above the pivot ceiling, stop looking
            if currentPrice > upper_limit:
                break
            
            # Check if price is within the "zone"
            if lower_limit <= currentPrice <= upper_limit:
                # Assuming validate_range_ceiling exists globally
                if validate_range_ceiling(HighPrices, i, j, upper_limit):
                    date_str = HighPrices.index[j].strftime('%Y-%m-%d')
                    tempResult.append((currentPrice, date_str, j))
                    tempIndexes.append(j)
                    # Skip ahead 20 days as per your original logic
                    j += 20 
                else:
                    break
            j += 1

        # A valid pivot group must have at least 3 points
        if len(tempResult) >= 3:
            indexToIgnore.update(tempIndexes)
            pivotsHigh.append(tempResult)

    # 2. Filter the results
    try:
        # We pass HighPrices directly to your existing filtering functions
        pivotsHigh_filtered = filterPivotsHigh(pivotsHigh, HighPrices)
        pivotsHighNotCurrent = filterPivotsHighNotReadyForEntry(pivotsHigh, HighPrices)
        
        return {
            "Ready": pivotsHigh_filtered,
            "NotReady": pivotsHighNotCurrent
        }
    except Exception as e:
        print(f"Error in filtering for {stock.ticker}: {e}")
        return {"Ready": [], "NotReady": []}

def filterPivotsLow(pivotsLow, pricesLow):
    """
    Returns pivots where:
    1. Every price since the pivot stayed above 97% of the original price.
    2. The CURRENT price is within 3% of the original price (Ready for entry).
    """
    filteredPivots = []
    for pivot in pivotsLow:
        # pivot[0][0] is price, pivot[0][2] is index i
        originalPrice = pivot[0][0] 
        start_idx = pivot[0][2]
        
        # Slice the series from the start of this pivot to today
        updatedPrices = pricesLow.iloc[start_idx:]
        
        # Use .all() on the pandas comparison for speed and safety
        if (updatedPrices >= 0.97 * originalPrice).all():
            # Check last price (Ready for entry)
            last_price = updatedPrices.iloc[-1]
            # Handle if last_price is somehow a series
            last_price_val = last_price.item() if hasattr(last_price, 'item') else last_price
            
            if last_price_val <= 1.03 * originalPrice:
                filteredPivots.append(pivot)
    return filteredPivots

def filterPivotsLowNotReadyForEntry(pivotsLow, pricesLow):
    """
    Returns pivots where price stayed above 97% of the floor, 
    but we don't care if it's currently near the entry point.
    """
    filteredPivots = []
    for pivot in pivotsLow:
        originalPrice = pivot[0][0]
        start_idx = pivot[0][2]
        
        updatedPrices = pricesLow.iloc[start_idx:]
        
        # Verify the floor was never significantly breached
        if (updatedPrices >= 0.97 * originalPrice).all():
            filteredPivots.append(pivot)
    return filteredPivots

def validate_range_floor(price_series, start_idx, current_idx, floor_threshold):
    """
    Slices the data and checks if the minimum price in that range 
    stayed above the floor.
    """
    # Slice the range
    subset = price_series.iloc[start_idx : current_idx + 1]
    
    # Get the minimum value
    min_val = subset.min()
    
    # Convert to scalar if it's a pandas object to prevent 500 errors
    min_val_scalar = min_val.item() if hasattr(min_val, 'item') else min_val
    
    return min_val_scalar > floor_threshold


def findLowPivots(stock: StockInfo):
    """
    Finds support pivot points using 1-year low prices from the StockInfo object.
    Logic: Looks for at least 3 points where price stays within a 1.3% floor.
    """
    # 1. Access the 1-year low prices from the class
    pricesLow = stock.low_prices_1y
    
    # Safety Check: Ensure data exists
    if pricesLow is None or len(pricesLow) == 0:
        return {"Ready": [], "NotReady": []}
    
    pivotsLow = []
    n = len(pricesLow)
    indexToIgnore = set()  # Using a set for faster 'in' checks

    # Main logic loop
    for i in range(n):
        if i in indexToIgnore:
            continue
            
        # Access price and date from the Series
        originalPricePoint = pricesLow.iloc[i]
        originalDatePoint = pricesLow.index[i]
        
        # Support Logic: 1.3% Buffer
        floor_limit = 0.987 * originalPricePoint
        ceiling_limit = 1.013 * originalPricePoint
        
        tempResult = []
        # Store as (Price, DateString, Index)
        tempResult.append((originalPricePoint, originalDatePoint.strftime('%Y-%m-%d'), i))
        
        j = i + 6 
        tempIndexes = [i]
        
        while j < n:
            if j in indexToIgnore:
                j += 1
                continue
            
            currentPrice = pricesLow.iloc[j]
            
            # If price drops BELOW the floor, the support is broken
            if currentPrice < floor_limit:
                break
            
            # If price stays within the "support zone" (+/- 1.3%)
            if floor_limit <= currentPrice <= ceiling_limit:
                # Assuming validate_range_floor is defined in your environment
                if validate_range_floor(pricesLow, i, j, floor_limit):
                    date_str = pricesLow.index[j].strftime('%Y-%m-%d')
                    tempResult.append((currentPrice, date_str, j))
                    tempIndexes.append(j)
                    # Skip 20 days to find distinct touches of support
                    j += 20 
                else:
                    break
            j += 1

        # Must have at least 3 touches to be a valid pivot group
        if len(tempResult) >= 3:
            indexToIgnore.update(tempIndexes)
            pivotsLow.append(tempResult)

    # 2. Filtering phase
    try:
        # Pass the results to your existing filtering helpers
        pivotsLow_filtered = filterPivotsLow(pivotsLow, pricesLow)
        pivotsLowNotCurrent = filterPivotsLowNotReadyForEntry(pivotsLow, pricesLow)
        
        return {
            "Ready": pivotsLow_filtered, 
            "NotReady": pivotsLowNotCurrent
        }
    except Exception as e:
        print(f"Error in filtering low pivots for {stock.ticker}: {e}")
        return {"Ready": [], "NotReady": []}

def filterPivotsHigh(pivotsHigh, pricesHigh):
    """
    Returns pivots where:
    1. Every price since the pivot stayed below 103% of original (no massive breakout).
    2. The CURRENT price is within 3% of the original price (Ready for entry).
    """
    filteredPivots = []
    for pivot in pivotsHigh:
        # pivot[0][0] is the original price, pivot[0][2] is the index 'i'
        originalPrice = pivot[0][0] 
        start_idx = pivot[0][2]
        
        # FIX: Slice the ACTUAL price series (Pandas), not the pivots list
        updatedPrices = pricesHigh.iloc[start_idx:]
        
        # Check if all subsequent prices stayed below the breakout threshold
        if (updatedPrices <= 1.03 * originalPrice).all():
            # Get the very last price to see if we are currently near the pivot
            last_price = updatedPrices.iloc[-1]
            last_price_val = last_price.item() if hasattr(last_price, 'item') else last_price
            
            # Ready for entry if price is at least 97% of the pivot price
            if last_price_val >= 0.97 * originalPrice:
                filteredPivots.append(pivot)
    return filteredPivots

def filterPivotsHighNotReadyForEntry(pivotsHigh, pricesHigh):
    """
    Returns pivots that:
    1. Haven't broken out more than 3% since they were formed.
    2. The current price is within 10% of the pivot price (not too far below).
    """
    filteredPivots = []
    
    current_price = pricesHigh.iloc[-1]
    for pivot in pivotsHigh:
        originalPrice = pivot[0][0]
        start_idx = pivot[0][2]

        updatedPrices = pricesHigh.iloc[start_idx:]
        not_broken_out = (updatedPrices <= 1.03 * originalPrice).all()
        within_10_percent = (current_price >= 0.90 * originalPrice)

        if not_broken_out and within_10_percent:
            filteredPivots.append(pivot)
    return filteredPivots

def validate_range_ceiling(price_series, start_idx, current_idx, ceiling_threshold):
    """
    Checks if the maximum price in the range stayed below the ceiling.
    """
    subset = price_series.iloc[start_idx : current_idx + 1]
    max_val = subset.max()
    
    # Extraction safety to prevent "Ambiguous truth value" 500 errors
    max_val_scalar = max_val.item() if hasattr(max_val, 'item') else max_val
    
    return max_val_scalar < ceiling_threshold
    



#------------------------------------------------------------ things with averages/ easy things ---------------------------------

def Close_to_avg_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT ARE CLOSE TO 150$ PRICE
    """this method tajes the stocks in 4% of each average and adds them to the list: like this
    [150,200]
    """
    listPairs=[]
    listofResults=[]
    listAverages=[150,200]
    for avg in listAverages:
        for stock in listOfStocks:
            pair=Is_Stock_Close_to_avg(stock,avg)
            if(pair!=None):
                listPairs.append(pair)
        listofResults.append(listPairs)
        listPairs=[]
    return listofResults

def Far_From_20_Stocks(listOfStocks):
    listPairs=[]
    for stock in listOfStocks:
        pair=Is_Stock_Far_From_20(stock)
        if(pair!=None):
            listPairs.append(pair)
    return listPairs


def Is_Stock_Close_to_avg(stock, avg_window: int):
    """
    Uses the StockInfo object and Pandas Series to check if the 
    current price is within 4% of the SMA.
    """
    try:
       
        prices = stock.close_prices_1y
        if prices is None or len(prices) < avg_window:
            return None
        
        sma_val = prices.rolling(window=avg_window).mean().iloc[-1]
        
        current_price = prices.iloc[-1]
        
        lower_bound = sma_val * 0.96
        upper_bound = sma_val * 1.04
        
        if ((sma_val < current_price <= upper_bound) and stock.atr>3):
            return {"Ticker":stock.ticker,"Status": 'ABOVE',"ATR_Match":True}
        elif ((sma_val < current_price <= upper_bound) and stock.atr<=3):
            return {"Ticker":stock.ticker,"Status": 'ABOVE',"ATR_Match":False}
        
        elif ((lower_bound <= current_price <= sma_val)and stock.atr>3):
            return {"Ticker":stock.ticker,"Status": 'BELOW',"ATR_Match":True}
        elif ((lower_bound <= current_price <= sma_val)and stock.atr<=3):
            return {"Ticker":stock.ticker,"Status": 'BELOW',"ATR_Match":False}
        
        return None
            
    except Exception as e:
        ticker_name = getattr(stock, 'ticker', 'Unknown')
        print(f"Error calculating SMA for {ticker_name}: {e}")
        return None

def Is_Stock_Far_From_20(stock: StockInfo):
    """
    Checks if price is >7% away from the 20-day SMA using object data.
    """
    try:
        prices = stock.close_prices_1y
        
        if prices is None or len(prices) < 20:
            return None
        
        # Calculate 20-SMA from the existing Series
        sma_20 = prices.rolling(window=20).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        lower_bound = sma_20 * (1-(2*(stock.atr/100)))
        upper_bound = sma_20 * (1+(2*(stock.atr/100)))
        
        if current_price > upper_bound:
            # Note: Returning stock.ticker (string) for FastAPI JSON compatibility
            return (stock.ticker, 'ABOVE')
        elif current_price < lower_bound:
            return (stock.ticker, 'BELOW')
        
        return None
            
    except Exception as e:
        print(f"Error calculating 20-SMA for {stock.ticker}: {e}")
        return None
#------------------------------------------------------------ C&H things like depth between 2 Cup pivots/ handle pivots



""""
THIS METHOD IS GONNA GET A LOST OF STOCKS AND SCAN FOR C&H AND MIN/MAX PIVOTS AS SUPPORT AND RESISTANCE
WERE DOING THIS IN 1 METHOD BECAUSE I DONT WANT TO CALCULATE 
PIVOTS MULTIPLE TIMES,SO WE DOWNLOAD THE DATA ONCE AND SEND TO BOTH METHODS
"""
def Cup_Handle_Stocks_And_Pivot_Stocks(listOfStocks):
    ReadyMaxPivotStocks=[]
    ReadyMinPivotStocks=[]
    ReadyCupHandleStocks=[]

    for stock in listOfStocks:
        GeneralPivotsHigh=findHighPivots(stock)
        GeneralPivotsLow=findLowPivots(stock)
        C_H_Pivots=GeneralPivotsHigh["NotReady"]
        if(len(GeneralPivotsHigh["Ready"])!=0):
            ReadyMaxPivotStocks.append({"Stock":stock.ticker,"Data":GeneralPivotsHigh["Ready"]})
        if(len(GeneralPivotsLow["Ready"])!=0):
            ReadyMinPivotStocks.append({"Stock":stock.ticker,"Data":GeneralPivotsLow["Ready"]})
        
        flag=CheckCupHandle(stock,C_H_Pivots)
        if(flag["Bool"]):
            ReadyCupHandleStocks.append({"Stock":stock.ticker,"Data":flag["Result"]})
    return {"Support": ReadyMinPivotStocks,"Resistance": ReadyMaxPivotStocks, "Cup And Handle":ReadyCupHandleStocks}





def DepthBetweenHandlesAndPotential(stock: StockInfo, dateFirst, dateSecond):
    try:
        prices_subset = stock.close_prices_1y.loc[dateFirst:dateSecond]
        
        if prices_subset.empty:
            return None
            
        minPrice = prices_subset.min()
        priceFirst = prices_subset.iloc[0]
        priceSecond = prices_subset.iloc[-1]
        
        priceMax = max(priceFirst, priceSecond)
        depthPercent = (priceMax - minPrice) / priceMax * 100
        
        return [depthPercent, (priceMax - minPrice), depthPercent]
    except:
        return None




def CheckCupHandle(stock,pivotsNotReadyOfStock):
    filteredPivots=[]
    for pivot in pivotsNotReadyOfStock:
        if len(pivot)==3:
            filteredPivots.append(pivot)
    for i in range(len(filteredPivots)-1):
        dateFirst=filteredPivots[i][0][1]
        dateSecond=filteredPivots[i][1][1]
        dateThird=filteredPivots[i][2][1]
        depthPotentialOfCup=DepthBetweenHandlesAndPotential(stock,dateFirst,dateSecond)
        depthPotentialOfHandle=DepthBetweenHandlesAndPotential(stock,dateSecond,dateThird)
        if depthPotentialOfCup!=None and depthPotentialOfHandle!=None and depthPotentialOfCup[0]>=23 and depthPotentialOfHandle[0]>=6:
            return {"Bool":True,"Result":[dateFirst,dateSecond,dateThird]}
            
    return {"Bool":False}

#HELPER FUNCTIONS TO DO GENERAL THINGS LIKE FILTER AND STUFF

























































"""THIS IS GONNA BE THE ML PART, WERE GONNA SE WHAT PATTERNS LEAD TO SUCCESS AT THE SMA 20 TRADE
MEANING WHEN A STOCK IS FAR AND ITS LIKE A MAGNET WE CAN TRADE ON IT, FROM HERE BEGINS THE JOURNEY"""









