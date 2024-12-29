from fastapi import FastAPI, Query# type: ignore
from pydantic import BaseModel# type: ignore
from fastapi.responses import FileResponse # type: ignore
from fastapi.responses import StreamingResponse
import pandas as pd# type: ignore
import numpy as np# type: ignore
import yfinance as yf# type: ignore
from io import StringIO
from datetime import datetime, timedelta


description = """ 
                    🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊---🧊

                        Welcome to the Stock Breakout API! Use the `/generate_report/` endpoint to test your thesis.  
                                        
                        
                        You will be required to enter the following inputs:

                        | Field                          |     Format     | Description                                                                                      |
                        |--------------------------------|----------------|--------------------------------------------------------------------------------------------------|
                        | **ticker**                     |     String     | Name of the company you want to run analysis on.                                                 |
                        | **start_date**                 |     String     | Start Date from which day you want to start analysis FORMAT: 'YYYY-MM-DD'                        |
                        | **end_date**                   |     String     | End Date + 1 till which day you want to end analysis FORMAT: 'YYYY-MM-DD' e.g.,                  | 
                        |                                |                | if you want analysis till 15th December 2021 - '2021-12-16'                                      |
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


def calculate_breakouts(stock_data,extended_data,input_data):

    # Calculate 20-day moving average for volume,daily price change percentage and  volume threshold
    stock_data[('20_day_avg_volume', '')] = stock_data[('Volume', input_data.ticker)].rolling(window=20).mean()
    stock_data[('Daily_Change_%', '')] = stock_data[('Close', input_data.ticker)].pct_change() * 100
    stock_data[('volume_threshold', '')] = ( ((input_data.volume_threshold / 100) + 1) * stock_data[('20_day_avg_volume', '')] )

    # Add Breakout condition
    stock_data[('Breakout', '')] = (
        (stock_data[('Volume', input_data.ticker)] >= stock_data[('volume_threshold', '')]) &
        (stock_data[('Daily_Change_%', '')] >= input_data.price_change_threshold)
    )

    breakouts = []

    for index, row in stock_data[stock_data[('Breakout', '')]].iterrows():
        buy_date = index
        sell_date = buy_date + pd.Timedelta(days=input_data.holding_period)

        # Adjust sell_date to the next available trading day if it's not in extended_data
        if sell_date not in extended_data.index:
            future_dates = extended_data.index[extended_data.index > sell_date]
            if not future_dates.empty:
                print(sell_date,"-------------converted---------------" ,future_dates)
                sell_date = future_dates[0]  # Set to the next available trading day
            else:
                sell_date = None  # No valid future trading day available
        if sell_date is not None:
            buy_price = row[('Close', input_data.ticker)]
            sell_price = extended_data.loc[sell_date, ('Close', input_data.ticker)]
            return_pct = ((sell_price - buy_price) / buy_price) * 100
        else:
            sell_price = None
            return_pct = None

        breakouts.append({
            "Breakout_Date": buy_date.strftime('%Y-%m-%d'),
            "Buy_Price": buy_price,
            "Sell_Date": sell_date.strftime('%Y-%m-%d') if sell_date else None,
            "Sell_Price": sell_price,
            "Return_%": return_pct
        })

    # Convert breakouts list to a DataFrame for better display
    breakouts_df = pd.DataFrame(breakouts)
    breakouts_df.set_index("Breakout_Date", inplace=True)
    
    # Create new columns in stock_data for breakout information
    stock_data[('Sell_Date', '')] = np.nan
    stock_data[('Sell_Price', '')] = np.nan
    stock_data[('Return_%', '')] = np.nan

    # Fill in breakout information
    for index, row in breakouts_df.iterrows():
        if index in stock_data.index:
            stock_data.loc[index, ('Sell_Date', '')] = row['Sell_Date']
            stock_data.loc[index, ('Sell_Price', '')] = row['Sell_Price']
            stock_data.loc[index, ('Return_%', '')] = row['Return_%']

    # Fill NaN values with a specific value (e.g., 0) for the selected columns
    columns_to_fill = ['20_day_avg_volume', 'Daily_Change_%', 'volume_threshold', 'Sell_Price', 'Return_%']
    stock_data[columns_to_fill] = stock_data[columns_to_fill].fillna(0)
    stock_data['Sell_Date'] = stock_data['Sell_Date'].fillna('YYYY-MM-DD')
    
    return stock_data


@app.post("/generate_report/")
async def generate_report(input_data: BreakoutInput):
    # Calculate extended end date
    end_date = datetime.strptime(input_data.end_date, '%Y-%m-%d')
    today = datetime.now()

    extended_end_date = end_date + timedelta(days=input_data.holding_period + 1)
    if extended_end_date > today:
        extended_end_date = today

    # Download stock data
    stock_data = yf.download(
        tickers=input_data.ticker,
        start=input_data.start_date,
        end=input_data.end_date,
        prepost=True,
        back_adjust=True)

    # Fetch additional stock data for extended period
    extended_data = yf.download(
        tickers=input_data.ticker,
        start=input_data.start_date,
        end=extended_end_date.strftime('%Y-%m-%d'),
        prepost=True,
        back_adjust=True)

    if len(stock_data) < 20:
        return {"message":ValueError("Not enough data for calculations. Need at least 20 rows.")}

    if stock_data.empty:
        return {"message":ValueError("No data found for the specified ticker and date range.")}
    # Ensure index is in datetime format
    stock_data.index = pd.to_datetime(stock_data.index)
    extended_data.index = pd.to_datetime(extended_data.index)

    df_data = calculate_breakouts(stock_data,extended_data,input_data)

    # Convert DataFrame to CSV in memory
    csv_buffer = StringIO()
    df_data.to_csv(csv_buffer, index=True)
    # Reset the buffer to the start
    csv_buffer.seek(0)
    output_file = f"{input_data.ticker}_breakout_report.csv"

    # Return the CSV
    return StreamingResponse(csv_buffer, media_type='text/csv', headers={"Content-Disposition": f"attachment; filename={output_file}"})

@app.get("/basic_info/")
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
