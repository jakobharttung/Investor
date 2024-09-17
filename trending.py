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

# Streamlit app configuration
st.set_page_config(page_title="Investor Analysis App", layout="wide")
st.title("Investor Analysis App")

# Anthropic API key from Streamlit secrets
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=anthropic_api_key)

# Function to get stock data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")
    return data

# Function to identify crossover events
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

# Function to get news for a company
def get_company_news(ticker):
    stock = yf.Ticker(ticker)
    company_name = stock.info['longName']
    news = stock.news
    return news

# Function to get company info, financials, and balance sheet
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
def analyze_crossover(event_date, event_type, news, company_info):
    two_months_ago = event_date - timedelta(days=60)
    relevant_news = [n for n in news if two_months_ago <= datetime.fromtimestamp(n['providerPublishTime'], pytz.UTC) <= event_date]
    
    prompt = f"""As a financial investor, analyze the following crossover event and provide insights:

Event Date: {event_date}
Event Type: {event_type}

Relevant News:
{[n['title'] for n in relevant_news]}

Company Info:
{company_info}

Please provide notable events, facts, company communications such as product announcements, investor events, M&A news, or strategy changes that could explain this crossover. Focus on quantitative and qualitative outputs with concise answers."""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# St
