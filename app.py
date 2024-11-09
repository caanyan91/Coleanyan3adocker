import os
import csv
import pygal
import requests
from datetime import datetime
from flask import Flask, render_template, request, url_for, flash, redirect

# Flask app initialization Also the api vantage hit limit so I had to utilize different api key and use different ip
app = Flask(__name__)
app.secret_key = 'cole_anyan_032891'
API_KEY = "LHMNY671K1L8PG0O"
STATICFOLD = os.path.join(app.root_path, 'static')

# stock symbol csv
def load_stock_symbols():
    # Must create separate use files for docker and app.py (I should have not used csv )
    file_path = "/app/stocks.csv" if os.path.exists("/app/stocks.csv") else "C:\\Users\\Cole\\Downloads\\4320\\Stock_Data_Visualizer\\stocks.csv"
    stock_symbols = []
    print(f"Loading stock symbols from {file_path}...")

    try:
      with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)
        for row in reader: stock_symbols.append(row[0])  
      print(f"Loaded {len(stock_symbols)} stock symbols.")
    except FileNotFoundError:
      print(f"Error: The file {file_path} was not found.")
    except Exception as e: print(f"An error occurred while loading stock symbols: {e}")
    return stock_symbols

# Retrieve stock data from Alpha Vantage
def retrieve_stock_data(stock_symbol, time_function, beginning_date, ending_date):
    try:
      print(f"Retrieving data for {stock_symbol} from {beginning_date} to {ending_date}")
      start_date_input = datetime.strptime(beginning_date, "%Y-%m-%d")
      end_date_input = datetime.strptime(ending_date, "%Y-%m-%d")

      if end_date_input < start_date_input: raise ValueError("Start date must be before end date.")
    except ValueError as e:
      print(f"Error in date input: {e}")
      return None

    # Build URL for Alpha Vantage API
    url = (f"https://www.alphavantage.co/query?function={time_function}"
           f"&symbol={stock_symbol}&apikey={API_KEY}&outputsize=full&datatype=json")
    print(f"API URL: {url}")
    api_response = requests.get(url)

    if api_response.status_code == 200:
      stock_data = api_response.json()
      time_type = { "TIME_SERIES_DAILY": "Time Series (Daily)",
                    "TIME_SERIES_WEEKLY": "Weekly Time Series",
                    "TIME_SERIES_MONTHLY": "Monthly Time Series"
                  }.get(time_function)
      if not time_type: print("Time function not supported."); return None

      time_series_data = stock_data.get(time_type, {})
      date_range_data = {date: values for date, values in time_series_data.items()
                         if beginning_date <= date <= ending_date}
      if not date_range_data:
        print(f"No data found between {beginning_date} and {ending_date}.")
        return None
      print(f"Retrieved {len(date_range_data)} records.")
      return date_range_data
    else:
      print(f"Failed to retrieve data. HTTP Code: {api_response.status_code}")
      return None

# Chart generation
def generate_chart(data, chart_type, stock_symbol):
    chart_title = f"{stock_symbol} Stock Prices"
    chart = pygal.Bar(title=chart_title, show_legend=True) if chart_type == "1" else pygal.Line(title=chart_title, show_legend=True)

    dates = sorted(data.keys())
    open_prices = [float(data[date]['1. open']) for date in dates]
    high_prices = [float(data[date]['2. high']) for date in dates]
    low_prices = [float(data[date]['3. low']) for date in dates]
    close_prices = [float(data[date]['4. close']) for date in dates]
    chart.x_labels = dates; chart.add("Open", open_prices); chart.add("High", high_prices); chart.add("Low", low_prices); chart.add("Close", close_prices)
    return chart.render_data_uri()

# Flask route to display the chart
@app.route("/", methods=["GET", "POST"])
def display_chart():
    stock_symbols = load_stock_symbols()

    if request.method == "POST":
      stock_symbol = request.form.get("stock_symbol")
      chart_type = request.form.get("chart_type")
      time_function = request.form.get("time_function")
      start_date = request.form.get("beginning_date")
      end_date = request.form.get("ending_date")

      try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        if end_date_obj < start_date_obj: raise ValueError("End date must be after start date.")
      except ValueError as e:
        flash(str(e))
        return render_template('graphing.html', chart_data=None, stock_symbol=stock_symbol, chart_type=chart_type, time_function=time_function, start_date=start_date, end_date=end_date, stock_symbols=stock_symbols)

      stock_data = retrieve_stock_data(stock_symbol, time_function, start_date, end_date)
      if stock_data:
        chart_data_uri = generate_chart(stock_data, chart_type, stock_symbol)
        return render_template('graphing.html', chart_data=chart_data_uri, stock_symbol=stock_symbol, chart_type=chart_type,time_function=time_function, start_date=start_date, end_date=end_date, stock_symbols=stock_symbols)
      else:
        flash("No data available for the given stock symbol and date range.")
        return render_template('graphing.html', chart_data=None, stock_symbol=stock_symbol, chart_type=chart_type, time_function=time_function, start_date=start_date, end_date=end_date, stock_symbols=stock_symbols)
    return render_template("graphing.html", chart_data=None, stock_symbol="", stock_symbols=stock_symbols)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)