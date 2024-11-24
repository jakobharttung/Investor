import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="max")
    return data

def plot_candlestick_chart(data, time_period):
    filtered_data = data.iloc[-time_period:]
    fig = go.Figure(data=[go.Candlestick(
        x=filtered_data.index,
        open=filtered_data['Open'],
        high=filtered_data['High'],
        low=filtered_data['Low'],
        close=filtered_data['Close']
    )])
    fig.update_layout(title="Candlestick Chart", xaxis_title="Date", yaxis_title="Price")
    return fig

def detect_technical_patterns(data):
    analysis = []

    # Head and Shoulders
    def head_and_shoulders(data):
        rolling_high = data['High'].rolling(window=20).max()
        rolling_low = data['Low'].rolling(window=20).min()
        if rolling_high.iloc[-1] < rolling_high.iloc[-2] > rolling_high.iloc[-3]:
            return True
        return False

    # Inverse Head and Shoulders
    def inverse_head_and_shoulders(data):
        rolling_low = data['Low'].rolling(window=20).min()
        if rolling_low.iloc[-1] > rolling_low.iloc[-2] < rolling_low.iloc[-3]:
            return True
        return False

    # Cup and Handle
    def cup_and_handle(data):
        prices = data['Close']
        if len(prices) >= 30 and (prices.iloc[-1] > prices.iloc[-15]):
            return True
        return False

    # Shooting Star
    def shooting_star(data):
        body = data['Close'] - data['Open']
        wick = data['High'] - data['Close']
        if body.iloc[-1] < wick.iloc[-1] and wick.iloc[-1] > 2 * abs(body.iloc[-1]):
            return True
        return False

    # Analysis
    if head_and_shoulders(data):
        analysis.append({"Pattern": "Head and Shoulders", "Strategy": "Sell (Reversal pattern detected)"})
    if inverse_head_and_shoulders(data):
        analysis.append({"Pattern": "Inverse Head and Shoulders", "Strategy": "Buy (Bullish reversal pattern detected)"})
    if cup_and_handle(data):
        analysis.append({"Pattern": "Cup and Handle", "Strategy": "Buy (Continuation pattern detected)"})
    if shooting_star(data):
        analysis.append({"Pattern": "Shooting Star", "Strategy": "Sell (Bearish reversal pattern detected)"})

    # Add more patterns as needed
    return analysis

def fetch_financials(ticker):
    stock = yf.Ticker(ticker)
    try:
        revenue = stock.financials.loc["Total Revenue"].tail(3)
        net_income = stock.financials.loc["Net Income"].tail(3)
    except:
        revenue, net_income = None, None

    financials = {
        "Revenue (Last 3 Years)": revenue.apply(lambda x: f"${x:,.0f}").to_dict() if revenue is not None else "Data not available",
        "Net Income (Last 3 Years)": net_income.apply(lambda x: f"${x:,.0f}").to_dict() if net_income is not None else "Data not available",
        "P/E": stock.info.get("trailingPE", "N/A"),
        "Forward P/E": stock.info.get("forwardPE", "N/A"),
        "EPS": stock.info.get("trailingEps", "N/A"),
        "EPS Growth": stock.info.get("earningsGrowth", "N/A"),
        "ROIC": stock.info.get("returnOnEquity", "N/A")
    }
    return financials

# Streamlit App
st.title("Stock Investor App")

ticker = st.text_input("Enter a Stock Ticker (e.g., AAPL, MSFT, TSLA):", value="AAPL")

if ticker:
    try:
        # Fetch and Display Stock Data
        data = fetch_stock_data(ticker)
        time_period = st.slider("Select Time Period (Days):", min_value=10, max_value=len(data), value=60)
        fig = plot_candlestick_chart(data, time_period)
        st.plotly_chart(fig)

        # Analyze Technical Patterns
        st.subheader("Technical Analysis Patterns")
        patterns = detect_technical_patterns(data)
        if patterns:
            for pattern in patterns:
                st.write(f"**Pattern:** {pattern['Pattern']}")
                st.write(f"**Suggested Strategy:** {pattern['Strategy']}")
                st.write("---")
        else:
            st.write("No technical patterns detected for the selected time period.")

        # Fetch and Display Financials
        st.subheader("Key Financials")
        financials = fetch_financials(ticker)
        for key, value in financials.items():
            if isinstance(value, dict):
                st.write(f"**{key}:**")
                st.write({str(k): v for k, v in value.items()})
            else:
                st.write(f"**{key}:** {value}")
    except Exception as e:
        st.error(f"Error fetching data for ticker '{ticker}': {e}")
