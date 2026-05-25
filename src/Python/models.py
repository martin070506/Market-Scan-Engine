import pandas as pd
import yfinance as yf
import numpy as np
from dataclasses import dataclass
from typing import Optional
from typing import List
from pydantic import BaseModel
@dataclass
class StockInfo:
    ticker: str
    atr: float = 0.0
    high_prices_3y: Optional[pd.Series] = None
    close_prices_1y: Optional[pd.Series] = None
    low_prices_1y: Optional[pd.Series] = None

    def download_all_data(self):
        data = yf.download(self.ticker, period="3y", auto_adjust=True, progress=False)
        if data.empty:
            return
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        self.high_prices_3y = data['High']
        self.close_prices_1y = data['Close'].tail(365)
        self.low_prices_1y = data['Low'].tail(365)
        self.atr = self._calc_atr_internal()

    def _calc_atr_internal(self) -> float:
        try:
            data = yf.download(self.ticker, period="15d", auto_adjust=True, progress=False)
            if data.empty or len(data) < 15: return 0.0
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            close, high, low = data['Close'], data['High'], data['Low']
            tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
            atr_latest = ((tr.iloc[1:15].mean() * 13) + tr.iloc[-1]) / 14
            current_price = close.iloc[-1]
            
            if current_price == 0 or np.isnan(current_price): return 0.0
            res = (atr_latest / current_price) * 100.0
            return float(res) if not (np.isnan(res) or np.isinf(res)) else 0.0
        except:
            return 0.0

class MLRequest(BaseModel):
    tickers: List[str]
    username: str



