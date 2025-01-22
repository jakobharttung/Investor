import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Stock Analysis App", layout="wide")

# Title
st.title("Stock Market Analysis App")

# Create columns for input fields
col1, col2 = st.columns(2)

# Stock ticker input
with col1:
    ticker_symbol = st.text_input("Enter Stock Ticker", value="AAPL").upper()

# Time period selection
with col2:
    period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=3
    )

def get_support_resistance(df, window=20):
    """Calculate support and resistance levels"""
    pivots = []
    dates = []
    counter = 0
    
    for i in range(window, len(df)-window):
        if all(df['Low'][i] <= df['Low'][i-j] for j in range(1,window+1)) and \
           all(df['Low'][i] <= df['Low'][i+j] for j in range(1,window+1)):
            pivots.append(df['Low'][i])
            dates.append(df.index[i])
            counter += 1
        elif all(df['High'][i] >= df['High'][i-j] for j in range(1,window+1)) and \
             all(df['High'][i] >= df['High'][i+j] for j in range(1,window+1)):
            pivots.append(df['High'][i])
            dates.append(df.index[i])
            counter += 1
    
    return dates, pivots

try:
    # Get stock data
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period=period)
    
    if df.empty:
        st.error("No data found for the specified ticker symbol.")
    else:
        # Calculate Bollinger Bands
        df.ta.bbands(length=20, append=True)
        
        # Calculate support and resistance levels
        dates, pivots = get_support_resistance(df)
        
        # Create candlestick chart
        fig = go.Figure()
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candlestick'
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
        
        # Add support and resistance levels
        fig.add_trace(go.Scatter(
            x=dates,
            y=pivots,
            name='Support/Resistance',
            mode='markers',
            marker=dict(
                size=8,
                color='red',
                symbol='diamond'
            )
        ))
        
        # Update layout
        fig.update_layout(
            title=f'{ticker_symbol} Stock Price',
            yaxis_title='Price',
            xaxis_title='Date',
            template='plotly_dark',
            height=800
        )
        
        # Show plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Display additional information
        with st.expander("Stock Information"):
            info = stock.info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
            with col2:
                st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,}")
            with col3:
                st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Built with Streamlit, yfinance, and pandas-ta")
