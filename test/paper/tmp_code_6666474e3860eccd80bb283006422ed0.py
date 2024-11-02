import yfinance as yf
from datetime import datetime, timedelta

# Define the stock ticker 
ticker = 'NVDA'

# Calculate the date range for the past month
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')

# Retrieve historical stock prices using Yahoo Finance API
nvda_data = yf.download(ticker, start=start_date, end=end_date)

# Calculate the stock price performance (e.g., percentage change)
performance = ((nvda_data['Close'][-1] - nvda_data['Close'][0]) / nvda_data['Close'][0]) * 100

print(f"Over the past month, from {start_date} to {end_date}, Nvidia's stock price has changed by {performance:.2f}%")