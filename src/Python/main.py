# src/Python/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException,Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address  
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from src.Python import scanner_service
from src.Python import database
from src.Python.models import MLRequest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

RateLimiter=Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = RateLimiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "https://mar-stocks.netlify.app","http://127.0.0.1:5500","http://127.0.0.1:8000","http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)



# src/Python/main.py





@app.post("/run-ml-analysis")
@RateLimiter.limit("5/minute")  
async def run_ml_analysis(data: MLRequest,request: Request):
    try:
        # data.tickers is the list sent from the JS
        # Calling your Scan_Tickers function
        scanner_service.GlobalUserName_Var = data.username
        raw_results = scanner_service.Scan_Tickers(data.tickers)
        
        # Formatting results into a clean dictionary list
        # Expected raw_results: [("AAPL", 0.85), ("TSLA", 0.42)]
        formatted_results = [
            {"ticker": ticker, "probability": round(prob * 100, 2)} 
            for ticker, prob in raw_results
        ]
        
        # Sort by highest probability first
        formatted_results.sort(key=lambda x: x['probability'], reverse=True)
        
        return {"success": True, "results": formatted_results}
    except Exception as e:
        print(f"ML Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/upload")
@RateLimiter.limit("5/minute")  # <--- Make sure this exists!
async def upload_csv(request: Request,file: UploadFile = File(...)):
    # Your JS hits this first just to "check" the file
    return {"success": True}

@app.post("/run_logic")
@RateLimiter.limit("5/minute")  # <--- Make sure this exists!
async def run_scan(request: Request,file: UploadFile = File(...)):
    # Your JS hits this second to actually process data
    result_id = scanner_service.run_pipeline(file.file)
    return {"success": True, "result_id": result_id}

@app.get("/results/{result_id}/{category}")
@RateLimiter.limit("30/minute")  # <--- Make sure this exists!
async def get_results(result_id: str, category: str,request: Request):
    data = database.get_results(result_id)
    if not data:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # We look up the key EXACTLY as the JS sends it (e.g., 'cup-handle')
    stocks = data.get(category, [])
    return {"stocks": stocks}