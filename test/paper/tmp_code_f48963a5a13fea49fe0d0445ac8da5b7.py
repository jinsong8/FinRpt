import yfinance as yf
import pandas as pd

# Create a ticker object for NVIDIA
nvda = yf.Ticker("NVDA")

# Get the closing stock prices for October 6th and September 6th
october_6th_price = nvda.history(start="2024-10-06", end="2024-10-06")['Close'].iloc[0]
september_6th_price = nvda.history(start="2024-09-06", end="2024-09-06")['Close'].iloc[-1]

# Calculate the percentage change in stock price
percentage_change = ((october_6th_price - september_6th_price) / september_6th_price) * 100

# Retrieve market capitalization at the start of September
info = nvda.info
market_cap_september_start = info['marketCap']

# Print the results
print(f"NVIDIA's stock price on October 6, 2024: ${october_6th_price}")
print(f"NVIDIA's stock price on September 6, 2024: ${september_6th_price}")
print(f"Market capitalization at the start of September: ${market_cap_september_start}")
print(f"NVIDIA's stock price performance over the past month: {percentage_change:.2f}%")