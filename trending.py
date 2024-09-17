import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import anthropic
from ta.trend import MACD
import pytz

# Retrieve Anthropic API key from Streamlit secrets
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_stock_data(ticker, period="1y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def plot_candlestick(data):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
    fig.update_layout(title=f"Stock Price Chart", xaxis_title="Date", yaxis_title="Price")
    return fig

def identify_crossovers(data):
    macd = MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['Signal'] = macd.macd_signal()
    
    crossovers = []
    for i in range(1, len(data)):
        if data['MACD'].iloc[i-1] < data['Signal'].iloc[i-1] and data['MACD'].iloc[i] > data['Signal'].iloc[i]:
            crossovers.append((data.index[i], 'up'))
        elif data['MACD'].iloc[i-1] > data['Signal'].iloc[i-1] and data['MACD'].iloc[i] < data['Signal'].iloc[i]:
            crossovers.append((data.index[i], 'down'))
    
    return crossovers

def get_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    news = stock.news
    filtered_news = [item for item in news if start_date <= datetime.fromtimestamp(item['providerPublishTime']) <= end_date]
    return filtered_news

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

def analyze_crossover(crossover_info, news, company_info):
    prompt = f"""
    As a financial investor, analyze the following stock crossover event and related information:

    Crossover Event: {crossover_info}
    
    Recent News:
    {news}
    
    Company Information:
    {company_info}

    Please provide a focused explanation of notable events, facts, company communications such as product announcements, investor events, M&A news, or strategy changes that could explain this crossover. Avoid technical jargon about bullish or bearish moments, and instead focus on concrete business factors. Provide both quantitative and qualitative insights in your analysis.
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

st.title("Stock Analysis App")

ticker = st.text_input("Enter a stock ticker:", value="SAN.PA")

if ticker:
    data = get_stock_data(ticker)
    
    fig = plot_candlestick(data)
    
    crossovers = identify_crossovers(data)
    
    for date, direction in crossovers:
        fig.add_annotation(
            x=date,
            y=data.loc[date, 'High'] if direction == 'up' else data.loc[date, 'Low'],
            text="↑" if direction == 'up' else "↓",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="green" if direction == 'up' else "red"
        )
    
    st.plotly_chart(fig)
    
    company_info = get_company_info(ticker)
    
    for date, direction in crossovers:
        start_date = date - timedelta(days=60)
        news = get_news(ticker, start_date, date)
        
        crossover_info = f"Date: {date.strftime('%Y-%m-%d')}, Direction: {'Upward' if direction == 'up' else 'Downward'}"
        analysis = analyze_crossover(crossover_info, news, company_info)
        
        st.subheader(f"Crossover on {date.strftime('%Y-%m-%d')} ({'Upward' if direction == 'up' else 'Downward'})")
        st.write(analysis)

st.sidebar.write("This app analyzes stock data and provides insights on trend changes.")
