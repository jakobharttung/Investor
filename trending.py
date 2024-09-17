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

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

# Function to get stock data
def get_stock_data(ticker, period="2y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

# Function to calculate moving averages
def calculate_moving_averages(data, short_window=20, long_window=100):
    data['SMA50'] = data['Close'].rolling(window=short_window).mean()
    data['SMA200'] = data['Close'].rolling(window=long_window).mean()
    return data

# Function to identify golden and death crosses
def identify_crosses(data):
    data['Golden_Cross'] = (data['SMA50'] > data['SMA200']) & (data['SMA50'].shift(1) <= data['SMA200'].shift(1))
    data['Death_Cross'] = (data['SMA50'] < data['SMA200']) & (data['SMA50'].shift(1) >= data['SMA200'].shift(1))
    return data

# Function to create candlestick chart with crosses
def create_chart(data):
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(f'{ticker} Stock Price'))

    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Price'))

    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='50 Day MA', line=dict(color='blue', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name='200 Day MA', line=dict(color='red', width=1.5)))

    golden_crosses = data[data['Golden_Cross']]
    death_crosses = data[data['Death_Cross']]

    fig.add_trace(go.Scatter(x=golden_crosses.index, y=golden_crosses['Low'],
                             mode='markers', name='Golden Cross',
                             marker=dict(symbol='triangle-up', size=20, color='green')))

    fig.add_trace(go.Scatter(x=death_crosses.index, y=death_crosses['High'],
                             mode='markers', name='Death Cross',
                             marker=dict(symbol='triangle-down', size=20, color='red')))

    fig.update_layout(title=f'{ticker} Stock Analysis', xaxis_rangeslider_visible=False)
    return fig

# Function to get company information
def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

# Function to analyze crosses
def analyze_cross(cross_date, cross_type, company_info, news):
    three_months_before = cross_date - timedelta(days=90)
    relevant_news = [n for n in news if three_months_before <= datetime.fromtimestamp(n['providerPublishTime'], pytz.UTC) <= cross_date]
    
    prompt = f"""
    Analyze the following {cross_type} that occurred on {cross_date.strftime('%Y-%m-%d')} for the company {company_info['longName']}.
    Consider the following information and news from the three months preceding the cross:

    Company Information:
    {company_info}

    Relevant News:
    {relevant_news}

    Provide a short explanation of potential factors that might have influenced this {cross_type}.
    Focus on notable events, facts, company communications, product announcements, investor events, M&A news, or strategy changes. We are looking for information that would explain the change in stock price
    Avoid technical explanations about the cross itself being bullish or bearish.
    """
    st.write(prompt)
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# Streamlit app
st.title('Stock Analysis App')

ticker = st.text_input('Enter Stock Ticker:', 'SAN.PA').upper()

if ticker:
    data = get_stock_data(ticker)
    data = calculate_moving_averages(data)
    data = identify_crosses(data)

    fig = create_chart(data)
    st.plotly_chart(fig)
    st.write("getting company info")

    company_info, news = get_company_info(ticker)
    news = yf.Ticker("SAN.PA").news
    
    st.subheader('Cross Analysis')
    
    golden_crosses = data[data['Golden_Cross']]
    death_crosses = data[data['Death_Cross']]

    for date, row in golden_crosses.iterrows():
        explanation = analyze_cross(date, 'Golden Cross', company_info, news)
        st.write(f"**Golden Cross on {date.strftime('%Y-%m-%d')}**")
        st.write(explanation)
        st.write("---")

    for date, row in death_crosses.iterrows():
        explanation = analyze_cross(date, 'Death Cross', company_info, news)
        st.write(f"**Death Cross on {date.strftime('%Y-%m-%d')}**")
        st.write(explanation)
        st.write("---")
