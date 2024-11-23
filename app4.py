import streamlit as st
import yfinance as yf
from plotly import graph_objects as go
from anthropic import Anthropic, Client
import datetime

# Initialize Anthropics API Client
api_key = st.secrets["ANTHROPIC_API_KEY"]
client = Client(api_key=api_key)

MODEL = "claude-3-5-sonnet-20241022"
SYSTEM_PROMPT = """You are a financial investor. Respond with facts and focused messages as talking to a non-expert."""

# Default industry
DEFAULT_INDUSTRY = "semiconductors"

# Streamlit App Layout
st.title("Investor Analysis App")

# Entry Box
industry = st.text_input("Enter an industry or sub-industry:", value=DEFAULT_INDUSTRY)
st.write(f"Analyzing stocks for industry: **{industry}**")

# Call Anthropics for top 5 stock tickers
st.write("Retrieving top 5 stock tickers for the industry...")

def get_top_tickers(industry):
    prompt = f"""
    Given the industry or sub-industry '{industry}', provide a list of 5 stock tickers generally considered the most promising for investment. Please list only the tickers.
    """
    response = client.completions.create(
        model=MODEL,
        max_tokens=1000,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
    )
    return response["completion"].split()

tickers = get_top_tickers(industry)
st.write(f"Identified tickers: {', '.join(tickers)}")

# Retrieve and Display Stock Data
st.write("Fetching historical stock data...")

def get_historical_data(tickers):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2y", interval="1wk")
        data[ticker] = hist
    return data

historical_data = get_historical_data(tickers)

# Plot Line Chart with Period Selector
def plot_stock_data(historical_data):
    fig = go.Figure()
    for ticker, data in historical_data.items():
        fig.add_trace(go.Scatter(
            x=data.index, y=data['Close'], mode='lines', name=ticker
        ))

    fig.update_layout(
        title="Stock Price History (Weekly Close)",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,
        updatemenus=[{
            "buttons": [
                {"label": "1wk", "method": "relayout", "args": [{"xaxis.range": ["1 week"]}]},
                {"label": "1mo", "method": "relayout", "args": [{"xaxis.range": ["1 month"]}]},
                {"label": "1y", "method": "relayout", "args": [{"xaxis.range": ["1 year"]}]},
                {"label": "5y", "method": "relayout", "args": [{"xaxis.range": ["5 year"]}]},
            ]
        }]
    )
    st.plotly_chart(fig)

plot_stock_data(historical_data)

# Fetch financials, news, and recommendations
def get_detailed_info(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    info = stock.info
    news = stock.news
    return financials, info, news

def recommend_stock(tickers):
    details = []
    for ticker in tickers:
        financials, info, news = get_detailed_info(ticker)
        details.append({
            "ticker": ticker,
            "info": info,
            "news": news,
            "financials": financials,
        })
    prompt = f"""
    You are analyzing stocks: {tickers}. For each stock, evaluate the key financials, news, and relevant information. 
    Recommend the most promising stock and provide a short explanation.
    """
    response = client.completions.create(
        model=MODEL,
        max_tokens=1000,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
    )
    return response["completion"]

recommendation = recommend_stock(tickers)
st.write("### Recommendation")
st.write(recommendation)

# Candlestick Chart
def plot_candlestick(ticker):
    data = yf.Ticker(ticker).history(period="1y", interval="1d")
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
    )])
    fig.update_layout(
        title=f"Candlestick Chart for {ticker}",
        xaxis_title="Date",
        yaxis_title="Price",
    )
    st.plotly_chart(fig)

# Identify patterns in candlestick data
def identify_patterns(data):
    # Simplified pattern detection logic (replace with a library like TA-Lib for advanced patterns)
    patterns = []
    for i in range(1, len(data) - 1):
        if data["Open"].iloc[i] < data["Close"].iloc[i] > data["High"].iloc[i - 1]:
            patterns.append(("Bullish breakout", data.index[i]))
        elif data["Open"].iloc[i] > data["Close"].iloc[i] < data["Low"].iloc[i - 1]:
            patterns.append(("Bearish breakout", data.index[i]))
    return patterns

for ticker in tickers:
    st.write(f"### Candlestick Chart and Analysis for {ticker}")
    plot_candlestick(ticker)
    stock_data = yf.Ticker(ticker).history(period="1y", interval="1d")
    patterns = identify_patterns(stock_data)
    for pattern, date in patterns:
        st.write(f"- {pattern} on {date}")

st.write("App powered by Streamlit, YFinance, Plotly, and Anthropic.")
