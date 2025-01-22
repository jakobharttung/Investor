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
           all(df['Low'][i] <= df['Low'][i+j] for j in range(1,window+1))
