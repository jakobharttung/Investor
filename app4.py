import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")
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
    close_prices = data['Close']
    high_prices = data['High']
    low_prices = data['Low']
    open_prices = data['Open']

    # Head and Shoulders
    def head_and_shoulders():
        # Check for peak in the middle and two smaller peaks on either side
        if len(close_prices) >= 50:
            middle_peak = high_prices[-30]
            left_peak = max(high_prices[-50:-30])
            right_peak = max(high_prices[-30:])
            if middle_peak > left_peak and middle_peak > right_peak:
                return True, {"Middle Peak": middle_peak, "Left Peak": left_peak, "Right Peak": right_peak}
        return False, {}

    # Double Top
    def double_top():
        if len(close_prices) >= 50:
            recent_highs = high_prices[-50:].nlargest(2)
            if abs(recent_highs.iloc[0] - recent_highs.iloc[1]) / recent_highs.iloc[0] < 0.02:
                return True, {"High 1": recent_highs.iloc[0], "High 2": recent_highs.iloc[1]}
        return False, {}

    # Double Bottom
    def double_bottom():
        if len(close_prices) >= 50:
            recent_lows = low_prices[-50:].nsmallest(2)
            if abs(recent_lows.iloc[0] - recent_lows.iloc[1]) / recent_lows.iloc[0] < 0.02:
                return True, {"Low 1": recent_lows.iloc[0], "Low 2": recent_lows.iloc[1]}
        return False, {}

    # Shooting Star
    def shooting_star():
        body = abs(close_prices.iloc[-1] - open_prices.iloc[-1])
        wick = high_prices.iloc[-1] - close_prices.iloc[-1]
        if wick > 2 * body and close_prices.iloc[-1] < open_prices.iloc[-1]:
            return True, {"Body": body, "Wick": wick}
        return False, {}

    # Detect patterns
    hs, hs_params = head_and_shoulders()
    if hs:
        analysis.append({
            "Pattern": "Head and Shoulders",
            "Description": "A reversal pattern signaling the end of an uptrend.",
            "Time Period": "Last 50 days",
            "Key Parameters": hs_params,
            "Suggested Action": "Sell (Bearish Reversal)"
        })

    dt, dt_params = double_top()
    if dt:
        analysis.append({
            "Pattern": "Double Top",
            "Description": "A bearish reversal pattern formed after two peaks.",
            "Time Period": "Last 50 days",
            "Key Parameters": dt_params,
            "Suggested Action": "Sell (Bearish Reversal)"
        })

    db, db_params = double_bottom()
    if db:
        analysis.append({
            "Pattern": "Double Bottom",
            "Description": "A bullish reversal pattern formed after two troughs.",
            "Time Period": "Last 50 days",
            "Key Parameters": db_params,
            "Suggested Action": "Buy (Bullish Reversal)"
        })

    ss, ss_params = shooting_star()
    if ss:
        analysis.append({
            "Pattern": "Shooting Star",
            "Description": "A bearish reversal candlestick pattern.",
            "Time Period": "Last Day",
            "Key Parameters": ss_params,
            "Suggested Action": "Sell (Bearish Reversal)"
        })

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
                st.write(f"**Description:** {pattern['Description']}")
                st.write(f"**Time Period:** {pattern['Time Period']}")
                st.write(f"**Key Parameters:** {pattern['Key Parameters']}")
                st.write(f"**Suggested Action:** {pattern['Suggested Action']}")
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
