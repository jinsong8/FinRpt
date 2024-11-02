import yfinance as yf

# Define the ticker symbol and time period
ticker = "NVDA"
start_date = "2023-02-20"  # one month ago
end_date = "2023-03-20"  # today

# Fetch the historical stock data
data = yf.download(ticker, start=start_date, end=end_date)

print(data.head())  # print the first few rows of the dataframe