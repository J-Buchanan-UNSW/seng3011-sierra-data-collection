import yfinance as yf

# Define the ticker symbol for Apple
ticker = yf.Ticker("EB9.F")

# Fetch sustainability data
sustainability_data = ticker.sustainability

# Print the sustainability data
print(sustainability_data)