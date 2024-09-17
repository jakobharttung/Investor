import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pytz
from ta.trend import SMAIndicator

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

# Function to get stock data
def get_stock_data(ticker, period="18mo"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

# Function to identify crossover events
def identify_crossovers(data):
    sma20 = SMAIndicator(close=data['Close'], window=20).sma_indicator()
    sma50 = SMAIndicator(close=data['Close'], window=50).sma_indicator()
    
    crossovers = []
    for i in range(1, len(data)):
        if (sma20.iloc[i-1] <= sma50.iloc[i-1] and sma20.iloc[i] > sma50.iloc[i]):
            crossovers.append((data.index[i], 'up'))
        elif (sma20.iloc[i-1] >= sma50.iloc[i-1] and sma20.iloc[i] < sma50.iloc[i]):
            crossovers.append((data.index[i], 'down'))
    
    return crossovers, sma20, sma50

# Function to get news for a specific date range
def get_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    news = stock.news
    filtered_news = [n for n in news if start_date <= datetime.fromtimestamp(n['providerPublishTime']) <= end_date]
    return filtered_news

# Function to get company info
def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    return {
        'info': info,
        'financials': financials.to_dict(),
        'balance_sheet': balance_sheet.to_dict()
    }

# Function to analyze crossover events
def analyze_crossover(event, news, company_info):
    prompt = f"""
    Analyze the following stock crossover event and related information:

    Crossover Event:
    Date: {event[0]}
    Type: {event[1]}

    Recent News:
    {news}

    Company Information:
    {company_info}

    Please provide insights on notable events, facts, company communications, and their potential impact on the stock performance.
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

# Streamlit app
st.title("Stock Analysis App")

# Input for stock ticker
ticker = st.text_input("Enter stock ticker:", "AAPL")

if ticker:
    # Get stock data
    data = get_stock_data(ticker)

    # Identify crossovers
    crossovers, sma20, sma50 = identify_crossovers(data)

    # Create candlestick chart
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True)
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Candlestick'))

    # Add moving averages
    fig.add_trace(go.Scatter(x=data.index, y=sma20, name='SMA20', line=dict(color='blue', width=1)))
    fig.add_trace(go.Scatter(x=data.index, y=sma50, name='SMA50', line=dict(color='red', width=1)))

    # Add crossover events
    for date, direction in crossovers:
        color = 'green' if direction == 'up' else 'red'
        symbol = 'triangle-up' if direction == 'up' else 'triangle-down'
        fig.add_trace(go.Scatter(x=[date], y=[data.loc[date, 'Low'] if direction == 'up' else data.loc[date, 'High']],
                                 mode='markers',
                                 marker=dict(symbol=symbol, size=10, color=color),
                                 name=f'{direction.capitalize()} Crossover'))

    fig.update_layout(title=f'{ticker} Stock Analysis', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)

    # Analyze crossover events
    st.subheader("Crossover Event Analysis")
    for event in crossovers:
        st.write(f"Crossover on {event[0]}: {event[1].capitalize()}")
        
        # Get news for two months before the crossover
        start_date = event[0] - timedelta(days=60)
        news = get_news(ticker, start_date, event[0])
        
        # Get company info
        company_info = get_company_info(ticker)
        
        # Analyze the crossover event
        analysis = analyze_crossover(event, news, company_info)
        st.write(analysis)
        st.write("---")

else:
    st.write("Please enter a stock ticker to begin analysis.")
