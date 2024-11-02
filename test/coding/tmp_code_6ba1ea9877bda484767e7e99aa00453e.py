import matplotlib.pyplot as plt

# Plot the closing prices
plt.figure(figsize=(10, 6))
plt.plot(data['Close'])
plt.title('Nvidia Stock Price (Closing)')
plt.xlabel('Date')
plt.ylabel('Price ($)')
plt.grid(True)
plt.show()