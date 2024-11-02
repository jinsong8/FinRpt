import yfinance as yf
from datetime import datetime

# Define the stock ticker and date range
ticker = 'NVDA'
start_date = '2024-09-06'
end_date = '2024-10-06'

# Retrieve historical stock prices using Yahoo Finance API
nvda_data = yf.download(ticker, start=start_date, end=end_date)

# Calculate the stock price performance (e.g., percentage change)
performance = ((nvda_data['Close'][-1] - nvda_data['Close'][0]) / nvda_data['Close'][0]) * 100