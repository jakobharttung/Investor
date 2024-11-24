import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

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

def analyze_technical_patterns(data):
    analysis = []
    indicators = {
        "RSI": ta.momentum.RSIIndicator(data['Close']),
        "MACD": ta.trend.MACD(data['Close']),
        "Bollinger Bands": ta.volatility.BollingerBands(data['Close'])
    }

    # RSI
    rsi = indicators["RSI"].rsi()
    if rsi.iloc[-1] > 70:
        analysis.append({"Pattern": "RSI", "Period": "Last 14 days", "Key Parameter": rsi.iloc[-1], "Strategy": "Sell (Overbought)"})
    elif rsi.iloc[-1] < 30:
        analysis.append({"Pattern": "RSI", "Period": "Last 14 days", "Key Parameter": rsi.iloc[-1], "Strategy": "Buy (Oversold)"})

    # MACD
    macd = indicators["MACD"].macd_diff()
    if macd.iloc[-1] > 0:
        analysis.append({"Pattern": "MACD", "Period": "Last 26 days", "Key Parameter": macd.iloc[-1], "Strategy": "Buy (Uptrend)"})
    else:
        analysis.append({"Pattern": "MACD", "Period": "Last 26 days", "Key Parameter": macd.iloc[-1], "Strategy": "Sell (Downtrend)"})

    # Bollinger Bands
    bb = indicators["Bollinger Bands"]
    if data['Close'].iloc[-1] > bb.bollinger_hband().iloc[-1]:
        analysis.append({"Pattern": "Bollinger Bands", "Period": "Last 20 days", "Key Parameter": data['Close'].iloc[-1], "Strategy": "Sell (Overbought)"})
    elif data['Close'].iloc[-1] < bb.bollinger_lband().iloc[-1]:
        analysis.append({"Pattern": "Bollinger Bands", "Period": "Last 20 days", "Key Parameter": data['Close'].iloc[-1], "Strategy": "Buy (Oversold)"})
    
    return analysis

def fetch_financials(ticker):
    stock = yf.Ticker(ticker)
    financials = {
        "Revenue (Last 3 Years)": stock.financials.loc["Total Revenue"].tail(3),
        "Net Income (Last 3 Years)": stock.financials.loc["Net Income"].tail(3),
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
        patterns = analyze_technical_patterns(data)
        for pattern in patterns:
            st.write(f"**Pattern:** {pattern['Pattern']}")
            st.write(f"**Period:** {pattern['Period']}")
            st.write(f"**Key Parameter:** {pattern['Key Parameter']:.2f}")
            st.write(f"**Suggested Strategy:** {pattern['Strategy']}")
            st.write("---")

        # Fetch and Display Financials
        st.subheader("Key Financials")
        financials = fetch_financials(ticker)
        for key, value in financials.items():
            if isinstance(value, pd.Series):
                st.write(f"**{key}:**")
                st.write(value.to_dict())
            else:
                st.write(f"**{key}:** {value}")
    except Exception as e:
        st.error(f"Error fetching data for ticker '{ticker}': {e}")
