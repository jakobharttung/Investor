import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import os
from anthropic import Anthropic
from datetime import datetime, timedelta
import pandas_ta as ta

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="ytd")
    return data

def calculate_moving_averages(data):
    data['SMA50'] = ta.trend.sma_indicator(data['Close'], window=50)
    data['SMA200'] = ta.trend.sma_indicator(data['Close'], window=200)
    return data

def identify_crossovers(data):
    crossovers = []
    for i in range(1, len(data)):
        if data['SMA50'].iloc[i-1] <= data['SMA200'].iloc[i-1] and data['SMA50'].iloc[i] > data['SMA200'].iloc[i]:
            crossovers.append(('golden', data.index[i]))
        elif data['SMA50'].iloc[i-1] >= data['SMA200'].iloc[i-1] and data['SMA50'].iloc[i] < data['SMA200'].iloc[i]:
            crossovers.append(('death', data.index[i]))
    return crossovers

def get_news(ticker, date):
    start_date = date - timedelta(days=7)
    end_date = date + timedelta(days=7)
    stock = yf.Ticker(ticker)
    news = stock.news
    filtered_news = [item for item in news if start_date <= datetime.fromtimestamp(item['providerPublishTime']) <= end_date]
    return filtered_news

def analyze_reversal(ticker, reversal_type, date, news):
    prompt = f"""As a financial investor, analyze the {reversal_type} cross for {ticker} stock on {date}. 
    Consider the following news items:
    {news}
    
    Provide a concise explanation for this stock reversal, including both quantitative and qualitative factors. 
    Focus on the most relevant information and limit your response to 2-3 sentences."""

    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=150,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.replace("'", "\\'")

def create_candlestick_chart(data, crossovers, explanations):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'])])

    for i, (cross_type, date) in enumerate(crossovers):
        color = 'green' if cross_type == 'golden' else 'red'
        symbol = 'triangle-up' if cross_type == 'golden' else 'triangle-down'
        fig.add_trace(go.Scatter(
            x=[date],
            y=[data.loc[date, 'High'] if cross_type == 'golden' else data.loc[date, 'Low']],
            mode='markers+text',
            marker=dict(symbol=symbol, size=15, color=color),
            text=[explanations[i]],
            textposition='top center' if cross_type == 'golden' else 'bottom center',
            showlegend=False
        ))

    fig.update_layout(title=f'{ticker} Stock Price', xaxis_title='Date', yaxis_title='Price')
    return fig

st.title('Stock Trend Analysis')

ticker = st.text_input('Enter Stock Ticker:', value='AAPL')

if ticker:
    data = get_stock_data(ticker)
    data = calculate_moving_averages(data)
    crossovers = identify_crossovers(data)

    explanations = []
    for cross_type, date in crossovers:
        news = get_news(ticker, date)
        explanation = analyze_reversal(ticker, cross_type, date, news)
        explanations.append(explanation)

    fig = create_candlestick_chart(data, crossovers, explanations)
    st.plotly_chart(fig)

    st.subheader('Trend Reversals')
    for i, (cross_type, date) in enumerate(crossovers):
        st.write(f"{cross_type.capitalize()} Cross on {date.date()}: {explanations[i]}")
