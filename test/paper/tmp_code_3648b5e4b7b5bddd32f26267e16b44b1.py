import yfinance as yf

# Define the ticker symbol and date range
ticker = 'NVDA'
start_date = '2024-09-06'
end_date = '2024-10-06'

# Download the historical data
data = yf.download(ticker, start=start_date, end=end_date)

# Print the first and last rows of the dataframe to get the starting and ending stock prices
print(data.head(1))
print(data.tail(1))