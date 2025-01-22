import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(page_title="Stock Analysis App", layout="wide")
st.title("Stock Technical Analysis App")

# Create input section
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Enter Stock Ticker", value='AAPL').upper()

with col2:
    period_options = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
    period = st.selectbox("Select Time Period", period_options, index=4)

# Function to get stock data
@st.cache_data
def get_stock_data(symbol, period):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Get the data
df = get_stock_data(symbol, period)

if df is not None and not df.empty:
    # Calculate technical indicators
    # Moving averages
    df['SMA20'] = ta.sma(df['Close'], length=20)
    df['SMA50'] = ta.sma(df['Close'], length=50)
    
    # RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Bollinger Bands
    bb_bands = ta.bbands(df['Close'], length=20)
    df = pd.concat([df, bb_bands], axis=1)
    
    # Create candlestick chart
    fig = go.Figure()
    
    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    ))
    
    # Add moving averages
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA20'],
        name='SMA20',
        line=dict(color='orange')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA50'],
        name='SMA50',
        line=dict(color='blue')
    ))
    
    # Add Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BBU_20_2.0'],
        name='Upper BB',
        line=dict(color='gray', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BBL_20_2.0'],
        name='Lower BB',
        line=dict(color='gray', dash='dash'),
        fill='tonexty'
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} Stock Price',
        yaxis_title='Price',
        xaxis_title='Date',
        template='plotly_dark',
        height=800
    )
    
    # Show the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Show RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df.index,
        y=df['RSI'],
        name='RSI'
    ))
    
    # Add RSI levels
    fig_rsi.add_hline(y=70, line_color='red', line_dash='dash')
    fig_rsi.add_hline(y=30, line_color='green', line_dash='dash')
    
    fig_rsi.update_layout(
        title='RSI Indicator',
        yaxis_title='RSI',
        xaxis_title='Date',
        template='plotly_dark',
        height=400
    )
    
    st.plotly_chart(fig_rsi, use_container_width=True)
    
    # Technical Analysis Insights
    st.subheader("Technical Analysis Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Moving Average Analysis
        last_sma20 = df['SMA20'].iloc[-1]
        last_sma50 = df['SMA50'].iloc[-1]
        last_close = df['Close'].iloc[-1]
        
        st.write("Moving Averages Analysis:")
        if last_close > last_sma20 and last_close > last_sma50:
            st.write("📈 Price is above both MAs - Bullish")
        elif last_close < last_sma20 and last_close < last_sma50:
            st.write("📉 Price is below both MAs - Bearish")
        else:
            st.write("↔️ Price is between MAs - Neutral")
    
    with col2:
        # RSI Analysis
        last_rsi = df['RSI'].iloc[-1]
        
        st.write("RSI Analysis:")
        if last_rsi > 70:
            st.write("🔥 Overbought (RSI > 70)")
        elif last_rsi < 30:
            st.write("❄️ Oversold (RSI < 30)")
        else:
            st.write("✅ Neutral RSI")
    
    with col3:
        # Bollinger Bands Analysis
        last_bbu = df['BBU_20_2.0'].iloc[-1]
        last_bbl = df['BBL_20_2.0'].iloc[-1]
        
        st.write("Bollinger Bands Analysis:")
        if last_close > last_bbu:
            st.write("⚠️ Price above upper band")
        elif last_close < last_bbl:
            st.write("⚠️ Price below lower band")
        else:
            st.write("✅ Price within bands")

else:
    st.error("No data available for the selected stock symbol and period.")
