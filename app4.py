import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")  # Always fetch the last year of data
    return data

def plot_candlestick_chart(data, annotations):
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])

    # Add annotations for detected patterns
    for annotation in annotations:
        fig.add_annotation(
            x=annotation['Date'],
            y=annotation['Price'],
            text=annotation['Pattern'],
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40
        )

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
        if len(close_prices) >= 50:
            middle_peak_index = high_prices[-50:].idxmax()
            left_peak = max(high_prices[-50:middle_peak_index])
            right_peak = max(high_prices[middle_peak_index:])
            middle_peak = high_prices[middle_peak_index]
            if middle_peak > left_peak and middle_peak > right_peak:
                return middle_peak_index, {"Middle Peak": middle_peak, "Left Peak": left_peak, "Right Peak": right_peak}
        return None, {}

    # Double Top
    def double_top():
        if len(close_prices) >= 50:
            recent_highs = high_prices[-50:].nlargest(2)
            if abs(recent_highs.iloc[0] - recent_highs.iloc[1]) / recent_highs.iloc[0] < 0.02:
                return recent_highs.idxmax(), {"High 1": recent_highs.iloc[0], "High 2": recent_highs.iloc[1]}
        return None, {}

    # Double Bottom
    def double_bottom():
        if len(close_prices) >= 50:
            recent_lows = low_prices[-50:].nsmallest(2)
            if abs(recent_lows.iloc[0] - recent_lows.iloc[1]) / recent_lows.iloc[0] < 0.02:
                return recent_lows.idxmax(), {"Low 1": recent_lows.iloc[0], "Low 2": recent_lows.iloc[1]}
        return None, {}

    # Shooting Star
    def shooting_star():
        body = abs(close_prices.iloc[-1] - open_prices.iloc[-1])
        wick = high_prices.iloc[-1] - close_prices.iloc[-1]
        if wick > 2 * body and close_prices.iloc[-1] < open_prices.iloc[-1]:
            return close_prices.index[-1], {"Body": body, "Wick": wick}
        return None, {}

    # Detect patterns
    hs_date, hs_params = head_and_shoulders()
    if hs_date:
        analysis.append({
            "Pattern": "Head and Shoulders",
            "Description": "A reversal pattern signaling the end of an uptrend.",
            "Date": hs_date,
            "Price": hs_params["Middle Peak"],
            "Key Parameters": hs_params,
            "Suggested Action": "Sell (Bearish Reversal)"
        })

    dt_date, dt_params = double_top()
    if dt_date:
        analysis.append({
            "Pattern": "Double Top",
            "Description": "A bearish reversal pattern formed after two peaks.",
            "Date": dt_date,
            "Price": dt_params["High 1"],
            "Key Parameters": dt_params,
            "Suggested Action": "Sell (Bearish Reversal)"
        })

    db_date, db_params = double_bottom()
    if db_date:
        analysis.append({
            "Pattern": "Double Bottom",
            "Description": "A bullish reversal pattern formed after two troughs.",
            "Date": db_date,
            "Price": db_params["Low 1"],
            "Key Parameters": db_params,
            "Suggested Action": "Buy (Bullish Reversal)"
        })

    ss_date, ss_params = shooting_star()
    if ss_date:
        analysis.append({
            "Pattern": "Shooting Star",
            "Description": "A bearish reversal candlestick pattern.",
            "Date": ss_date,
            "Price": high_prices[ss_date],
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
        annotations = []

        # Analyze Technical Patterns
        st.subheader("Technical Analysis Patterns")
        patterns = detect_technical_patterns(data)
        if patterns:
            for pattern in patterns:
                st.write(f"**Pattern:** {pattern['Pattern']}")
                st.write(f"**Description:** {pattern['Description']}")
                st.write(f"**Date:** {pattern['Date'].strftime('%Y-%m-%d')}")
                st.write(f"**Key Parameters:** {pattern['Key Parameters']}")
                st.write(f"**Suggested Action:** {pattern['Suggested Action']}")
                st.write("---")
                annotations.append({"Pattern": pattern["Pattern"], "Date": pattern["Date"], "Price": pattern["Price"]})
        else:
            st.write("No technical patterns detected for the past year.")

        # Plot Candlestick Chart
        st.subheader("Candlestick Chart")
        zoom_period = st.slider("Select Time Period to Zoom (Days):", min_value=10, max_value=len(data), value=60)
        fig = plot_candlestick_chart(data.iloc[-zoom_period:], annotations)
        st.plotly_chart(fig)

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
