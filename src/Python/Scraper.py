from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
app = FastAPI()



# ✅ allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500","https://market-scan-engine.onrender.com"],
    allow_credentials=False,   # set True only if you use cookies/sessions
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- CSV validation ----------
def check_Correct_Format_CSV(f):
    try:
        print("hjadjhadhjaghgayhdgahgdhgahdghadghavhgaghdghgadh")
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



@app.post("/run_logic")
async def Run_Entire_Script(file: UploadFile=File(...)):
    listOfStocks =fromCSV_to_listOfStocks(file.file)

    return {"Cup_Handle":listOfStocks} # just some value so theres no syntax error





def fromCSV_to_listOfStocks(file):
    df = pd.read_csv(file)
    listOfStocks = df.values.tolist()
   
    print(listOfStocks)
    return listOfStocks





def Cup_Handle_Stocks(listOfStocks):
    #GETS A LIST OF STOCKS AND RETURNS THE ONES THAT HAVE CUP AND HANDLE PATTERN
    pass








def IsStock_Cup_Handle(stock):
    #GETS A STOCK TICKER(string) AND RETURNS TRUE IF IT HAS CUP AND HANDLE PATTERN
    pass




def Calculate_Pivots(stock):
    #GETS A STOCK TICKER(string) AND RETURNS PIVOTS AS A DICTIONARY [max/min pivot , date, price] for example [max, "2023-01-01", 150.0]
    pass
    









if __name__ == "__main__":
    import uvicorn
    import os
    host=os.getenv("APP_HOST","127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    print("hjadjhadhjaghgayhdgahgdhgahdghadghavhgaghdghgadh")
    uvicorn.run("Scraper:app", host=host, port=port, reload=True)