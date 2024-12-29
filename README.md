# Stock Breakout API
 A Python-based financial analysis tool to identify and evaluate stock breakout opportunities using custom thresholds for volume and price changes. This project demonstrates skills in API integration, handling financial data, preventing lookahead bias, and developing a simple, usable interface.

---

## **Project Description**

This mini project aims to test a stock breakout thesis:
- If a stock has a daily volume > **200% (X% customizable input)** of the average daily volume over the last 20 days **AND** its price is up at least **2% (Y% customizable input)** compared to the previous day, this indicates a potential "breakout." A buy signal is generated on the breakout day, and the stock is held for **10 days (Z customizable input)** before selling. The program should calculate the returns for each breakout event.

**Output**:
   - A downloadable CSV file with the following:
     - Dates that meet the breakout criteria ("Buy" days)
     - Sell Dates and Sell Price meet the breakout days
     - Return on investment for each breakout event after holding for Z days

---

## **API Endpoints**

### **`/generate_report/`**  

Use this endpoint to analyze stock data and generate reports.


| Field                      | Format        | Description                                                                                      |
|----------------------------|---------------|--------------------------------------------------------------------------------------------------|
| **ticker**                 | String        | Stock ticker symbol for (e.g., AAPL, TSLA) analysis.                                                               |
| **start_date**             | String        | Start date for analysis in `YYYY-MM-DD` format.                                                 |
| **end_date**               | String        | End date for analysis +1 in `YYYY-MM-DD` format (inclusive).                                        |
| **volume_threshold**       | Float         | Percent volume threshold for breakout detection (e.g., 200 for 200%).                           |
| **price_change_threshold** | Float         | Percent price increase threshold compared to the previous day (e.g., 2 for 2%).                 |
| **holding_period**         | Integer       | Number of days to hold the stock post-breakout.                                                 |



### UsageExample Inputs
```json
{
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "volume_threshold": 200,
    "price_change_threshold": 2,
    "holding_period": 10
}
```
---

## **Insights and Observations**

#### Sample Observations:

- Tickers Analyzed: AAPL, TSLA, ACM, ACI, AAL
  - **AAPL**: 2 breakouts, both negative with a maximum loss of -5%. Total return: **-7.8%**.
  - **TSLA**: 3 breakouts, 2 negative (max loss -5%) and 1 positive (5.9%). Total return: **-7.8%**.
  - **ACM**: 3 breakouts, mostly negative with a maximum loss of -10% and one positive (2%). Total return: **-10.2%**.
  - **ACI**: 12 breakouts, mixed with both positive and negative returns capped at 3%. Total return: **-7.6%**.
  - **AAL**: 8 breakouts, mostly negative with a maximum loss of -10% and one positive (7%). Total return: **-29.78%**.

#### **General Insights**:
  - Breakouts were sparse, but returns were moderate and mixed.
  - High sensitivity to breakout conditions, with holding period returns showing variability, more potential for returns if we lower the threshold.
  - Potential for improvement by introducing filters for broader market trends.
---
## Example Use Case

- **Objective**: Analyze stock performance using breakout signals.
- **Insights**: Evaluate whether breakout signals provide meaningful trading opportunities.
- **Future Enhancements**:
  - Incorporate additional filters such as RSI or MACD indicators.
  - Visualize breakout events with chart
  - Support batch processing of multiple tickers simultaneously.

---