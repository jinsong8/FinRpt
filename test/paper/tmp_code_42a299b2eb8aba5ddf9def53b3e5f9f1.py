import yfinance as yf
from datetime import datetime, timedelta

# Define the stock ticker and date range
ticker = 'NVDA'
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')

try:
    # Retrieve historical stock prices using Yahoo Finance API
    nvda_data = yf.download(ticker, start=start_date, end=end_date)
except Exception as e:
    print(f"Failed to retrieve data for {ticker}: {e}")
else:
    if nvda_data.empty:
        print("No data available for the specified date range.")
    else:
        # Calculate the stock price performance (e.g., percentage change)
        performance = ((nvda_data['Close'][-1] - nvda_data['Close'][0]) / nvda_data['Close'][0]) * 100
        print(f"The stock price of {ticker} has changed by {performance:.2f}% over the past month.")