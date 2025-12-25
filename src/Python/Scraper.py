import uuid
from fastapi import FastAPI, UploadFile, File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
app = FastAPI()



# ✅ allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "https://mar-stocks.netlify.app"],
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


results_cache={}
@app.post("/run_logic")
async def Run_Entire_Script(file: UploadFile=File(...)):
    listOfStocks =fromCSV_to_listOfStocks(file.file)
    List_Cup_Handle_Stocks=Cup_Handle_Stocks(listOfStocks)
    List_Double_Bottom_Stocks=Double_Bottom_Stocks(listOfStocks)
    List_Close_to_150_Stocks=Close_to_150_Stocks(listOfStocks)

    result_id=str(uuid.uuid4())
    results_cache[result_id]={
        "cup_handle": List_Cup_Handle_Stocks,
        "double_bottom": List_Double_Bottom_Stocks,
        "close_to_150": List_Close_to_150_Stocks
    }
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

@app.get("/results/{result_id}/close-to-150")
async def get_close_to_150(result_id: str):
    if result_id not in results_cache:
        raise HTTPException(status_code=404, detail="Results not found")
    return {"stocks": results_cache[result_id]["close_to_150"]}



def fromCSV_to_listOfStocks(file):
    df = pd.read_csv(file)
    listOfStocks = df.values.tolist()
   
    print(listOfStocks)
    return listOfStocks





def Cup_Handle_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT HAVE CUP AND HANDLE PATTERN
    return listOfStocks





def IsStock_Cup_Handle(stock):
    #GETS A STOCK TICKER(string) AND RETURNS TRUE IF IT HAS CUP AND HANDLE PATTERN
    pass


def Double_Bottom_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT HAVE DOUBLE BOTTOM PATTERN
    return listOfStocks
def IsStock_Double_Bottom(stock):
    #GETS A STOCK TICKER(string) AND RETURNS TRUE IF IT HAS DOUBLE BOTTOM PATTERN
    pass

def Close_to_150_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT ARE CLOSE TO 150$ PRICE
    return listOfStocks


def IsStock_Close_to_150(stock):
    #GETS A STOCK TICKER(string) AND RETURNS TRUE IF IT IS CLOSE TO 150$ PRICE
    pass




def Calculate_Pivots(stock):
    #GETS A STOCK TICKER(string) AND RETURNS PIVOTS AS A DICTIONARY [max/min pivot , date, price] for example [max, "2023-01-01", 150.0]
    pass
    









