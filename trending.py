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

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")
    return data

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

def analyze_crossover(crossover_date, direction, news, company_info):
    prompt = f"""
    As a financial investor, analyze the following information:

    Crossover event on {crossover_date}, direction: {direction}

    Recent news:
    {news}

    Company information:
    {company_info}

    Provide a focused explanation for this crossover event, considering notable events, facts, company communications, product announcements, investor events, M&A news, or strategy changes that could explain the crossover. Do not focus on technical analysis terminology.

    Provide a concise response with quantitative and qualitative insights.
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert.",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

st.title("Investor Analysis App")

ticker = st.text_input("Enter a stock ticker:")

if ticker:
    data = get_stock_data(ticker)
    crossovers = identify_crossovers(data)

    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'])])

    for date, direction in crossovers:
        color = 'green' if direction == 'up' else 'red'
        symbol = 'triangle-up' if direction == 'up' else 'triangle-down'
        fig.add_trace(go.Scatter(x=[date], y=[data['Low'][date]],
                                 mode='markers',
                                 marker=dict(symbol=symbol, size=15, color=color),
                                 showlegend=False))

    st.plotly_chart(fig)

    company_info = get_company_info(ticker)

    for date, direction in crossovers:
        start_date = date - timedelta(days=60)
        end_date = date
        news = get_news(ticker, start_date.replace(tzinfo=pytz.UTC), end_date.replace(tzinfo=pytz.UTC))
        
        analysis = analyze_crossover(date, direction, news, company_info)
        
        st.subheader(f"Crossover on {date.date()}, Direction: {direction}")
        st.write(analysis)
