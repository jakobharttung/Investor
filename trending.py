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

def get_stock_data(ticker, period="2y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def calculate_moving_averages(data, short_window=50, long_window=200):
    data['SMA50'] = data['Close'].rolling(window=short_window).mean()
    data['SMA200'] = data['Close'].rolling(window=long_window).mean()
    return data

def identify_crossovers(data):
    data['Golden_Cross'] = (data['SMA50'] > data['SMA200']) & (data['SMA50'].shift(1) <= data['SMA200'].shift(1))
    data['Death_Cross'] = (data['SMA50'] < data['SMA200']) & (data['SMA50'].shift(1) >= data['SMA200'].shift(1))
    return data

def create_candlestick_chart(data, crossovers):
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(f"{ticker} Stock Price"))

    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name="Candlesticks"))

    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="50-day SMA", line=dict(color='blue', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name="200-day SMA", line=dict(color='red', width=1.5)))

    for idx, row in crossovers[crossovers['Golden_Cross']].iterrows():
        fig.add_annotation(x=idx, y=row['Low'], text="↑", showarrow=False, font=dict(size=20, color="green"))

    for idx, row in crossovers[crossovers['Death_Cross']].iterrows():
        fig.add_annotation(x=idx, y=row['High'], text="↓", showarrow=False, font=dict(size=20, color="red"))

    fig.update_layout(height=600, width=1000, title_text=f"{ticker} Stock Analysis")
    return fig

def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return info

def get_company_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    news = stock.news
    filtered_news = [item for item in news if start_date <= datetime.fromtimestamp(item['providerPublishTime']) <= end_date]
    return filtered_news

def analyze_reversal(ticker, date, crossover_type, company_info, news):
    prompt = f"""As a financial investor, analyze the {crossover_type} that occurred on {date} for {ticker}. 
    Consider the following company information and relevant news:

    Company Information:
    {company_info}

    Relevant News:
    {news}

    Provide a focused explanation for this stock trend reversal, including notable events, facts, or company communications that could explain the change. 
    Avoid technical jargon about crossovers and focus on fundamental factors that might have influenced the stock's direction.
    Limit your response to 3-4 sentences."""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        temperature=0.7,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

st.title("Stock Analysis App")

ticker = st.text_input("Enter a stock ticker:", value="AAPL").upper()

if ticker:
    data = get_stock_data(ticker)
    data = calculate_moving_averages(data)
    data = identify_crossovers(data)

    crossovers = data[(data['Golden_Cross'] | data['Death_Cross'])]

    fig = create_candlestick_chart(data, crossovers)
    st.plotly_chart(fig)

    company_info = get_company_info(ticker)
    start_date = data.index[0].to_pydatetime()
    end_date = data.index[-1].to_pydatetime()
    news = get_company_news(ticker, start_date, end_date)

    st.subheader("Trend Reversal Explanations")

    for idx, row in crossovers.iterrows():
        crossover_type = "Golden Cross" if row['Golden_Cross'] else "Death Cross"
        date = idx.strftime("%Y-%m-%d")
        
        relevant_news = [item for item in news if abs((datetime.fromtimestamp(item['providerPublishTime']) - idx.to_pydatetime()).days) <= 7]
        
        explanation = analyze_reversal(ticker, date, crossover_type, company_info, relevant_news)
        
        st.write(f"**{crossover_type} on {date}:**")
        st.write(explanation)
        st.write("---")
