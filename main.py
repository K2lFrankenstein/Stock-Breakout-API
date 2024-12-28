from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import FileResponse
import yfinance as yf
import pandas as pd
import csv


description = """ 
                    🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊

                        Welcome to the Stock Breakout API! Use the `/generate_report/` endpoint to test your thesis.  
                                        
                        
                        You will be required to enter the following inputs:

                        | Field                          |     Format     | Description                                                                                      |
                        |--------------------------------|----------------|--------------------------------------------------------------------------------------------------|
                        | **ticker**                     |     String     | Name of the company you want to run analysis on.                                                 |
                        | **start_date**                 |     String     | Start Date from which day you want to start analysis FORMAT: 'YYYY-MM-DD'                        |
                        | **end_date**                   |     String     | End Date + 1 till which day you want to end analysis FORMAT: 'YYYY-MM-DD' e.g.,                  | 
                        |                                |                |  if you want analysis till 15th December 2021 - '2021-12-16'                                     |
                        | **volume_threshold**           |     Float      | Variation in volume you want to capture for 20 day window, e.g., 200 for 200%                    |
                        | **price_change_threshold**     |     Float      | Variation in price you want from previous day, e.g., 2 for 2%                                    |
                        | **holding_period**             |     Intiger    | Number of days you want to hold the stock after breakout                                         |
                        

                    🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊

👨‍💻️👨‍💻️👨‍💻️ By :- `Ketul Patel`  

Find the Source code at: `https://github.com/K2lFrankenstein/` 
"""

app = FastAPI(title="Stock Breakout API!",
    description=description,
    version="1.0.4",openapi_url="/base_schema",docs_url="/")

class BreakoutInput(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    volume_threshold: float  # e.g., 200 for 200%
    price_change_threshold: float  # e.g., 2 for 2%
    holding_period: int  # e.g., 10 days


def calculate_breakouts(data, volume_threshold, price_change_threshold, holding_period):
    # Calculate 20-day moving average for volume
    data['20_day_avg_volume'] = data['Volume'].rolling(window=20).mean()
    
    # Calculate daily price change percentage
    data['Daily_Change_%'] = data['Close'].pct_change() * 100

    # Identify breakout days
    data['Breakout'] = (
        (data['Volume'] > (volume_threshold / 100) * data['20_day_avg_volume']) &
        (data['Daily_Change_%'] > price_change_threshold)
    )

    breakouts = []

    for index, row in data.iterrows():
        if row['Breakout']:
            buy_date = index
            sell_date = index + pd.Timedelta(days=holding_period)

            if sell_date in data.index:
                buy_price = row['Close']
                sell_price = data.loc[sell_date, 'Close']
                return_pct = ((sell_price - buy_price) / buy_price) * 100
            else:
                return_pct = None  # Insufficient data for holding period

            breakouts.append({
                "Breakout_Date": buy_date,
                "Buy_Price": buy_price,
                "Sell_Date": sell_date if sell_date in data.index else None,
                "Sell_Price": sell_price if sell_date in data.index else None,
                "Return_%": return_pct
            })

    return breakouts


@app.post("/generate_report/")
async def generate_report(input_data: BreakoutInput):
    # Fetch stock data
    stock_data = yf.download(tickers=input_data.ticker, interval='1d',start= input_data.start_date, end=input_data.end_date, prepost =True,back_adjust =True)

    if stock_data.empty:
        return {"error": "No data found for the specified ticker and date range."}

    # Process data
    breakouts = calculate_breakouts(
        stock_data,
        input_data.volume_threshold,
        input_data.price_change_threshold,
        input_data.holding_period
    )

    # Generate CSV
    output_file = f"{input_data.ticker}_breakout_report.csv"
    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Breakout_Date", "Buy_Price", "Sell_Date", "Sell_Price", "Return_%"])
        writer.writeheader()
        writer.writerows(breakouts)

    return FileResponse(output_file, media_type="text/csv", filename=output_file)


@app.get("/")
def read_root():
    return {"message": """
    Welcome to the Stock Breakout API! Use the /generate_report/ endpoint to test your thesis.

    You will be required to enter the following inputs:
    - **ticker**: `str` (Name of the company you want to run analysis on)
    - **start_date**: `str` (Start Date from which day you want to start analysis FORMAT: 'YYYY-MM-DD')
    - **end_date**: `str` (End Date + 1 till which day you want to end analysis FORMAT: 'YYYY-MM-DD' e.g., if you want analysis till 15th December 2021 - '2021-12-16')
    - **volume_threshold**: `float` (Variation in volume you want to capture for 20 day window, e.g., 200 for 200%)
    - **price_change_threshold**: `float` (Variation in price you want from previous day, e.g., 2 for 2%)
    - **holding_period**: `int` (Number of days you want to hold the stock after breakout)
    """}


start_date = '2024-11-01'
end_date = '2024-11-21'
ticker_symbol = "MSFT" #'NVDA'
# volume_threshold: float  # e.g., 200 for 200%
# price_change_threshold: float  # e.g., 2 for 2%
# holding_period: int  # e.g., 10 days

data = yf.download(tickers=ticker_symbol, interval='1d',start= start_date, end=end_date, prepost =True,back_adjust =True)



# Display a summary of the fetched data
print(f"Summary of Historical Data for {ticker_symbol}:")
print(data)