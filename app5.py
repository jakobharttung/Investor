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
    st.error("No data available for the selected stock symbol and period.")import streamlit as st
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
