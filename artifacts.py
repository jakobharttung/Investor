import streamlit as st
import yfinance as yf
import pygwalker as pyg
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

def get_stock_data(ticker, period="10y", interval="1d"):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3650)  # Approximately 10 years
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            st.error(f"No data available for {ticker}. This could be due to an invalid ticker symbol or a temporary issue with the data provider.")
            return None
        
        return data[['Open', 'High', 'Low', 'Close']]  # Select only required columns
    except Exception as e:
        st.error(f"An error occurred while fetching data: {str(e)}")
        return None

st.set_page_config(layout="wide")
st.title("My First Artifacts App")

# Sidebar for user input
with st.sidebar:
    ticker = st.text_input("Enter stock ticker (e.g., AAPL, GOOGL):", "AAPL")
    fetch_data = st.button("Fetch Data")

# Main content
if fetch_data:
    # Fetch initial data
    with st.spinner("Fetching 10 years of daily stock data..."):
        df = get_stock_data(ticker)
    
    if df is not None and not df.empty:
        st.success(f"Data fetched for {ticker} (10 years of daily data)")
        st.write(f"Data range: from {df.index.min()} to {df.index.max()}")
        st.write(f"Number of data points: {len(df)}")
        
        # Create tabs
        tab1, tab2 = st.tabs(["PyGWalker Analysis", "Candlestick Chart"])
        
        with tab1:
            st.header("Interactive Analysis with PyGWalker")
            pyg_html = pyg.to_html(df)
            st.components.v1.html(pyg_html, height=600)
        
        with tab2:
            st.header("Candlestick Chart")
            
            # Date range selection
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", min(df.index).date(), min_value=min(df.index).date(), max_value=max(df.index).date())
            with col2:
                end_date = st.date_input("End Date", max(df.index).date(), min_value=min(df.index).date(), max_value=max(df.index).date())
            
            # Filter data based on selected date range
            mask = (df.index.date >= start_date) & (df.index.date <= end_date)
            filtered_df = df.loc[mask]
            
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(x=filtered_df.index,
                                                 open=filtered_df['Open'],
                                                 high=filtered_df['High'],
                                                 low=filtered_df['Low'],
                                                 close=filtered_df['Close'])])
            fig.update_layout(title=f"{ticker} Stock Price", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please try a different ticker symbol or check your internet connection.")
else:
    st.info("Enter a stock ticker and click 'Fetch Data' to begin.")

# Display yfinance version
st.sidebar.write(f"yfinance version: {yf.__version__}")
