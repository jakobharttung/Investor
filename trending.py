import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import ta

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_stock_data(ticker, period="2y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
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

def create_candlestick_chart(data, crossovers):
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(f"Candlestick Chart for {ticker}",))

    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name="Candlesticks"))

    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="50-day SMA", line=dict(color='blue', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name="200-day SMA", line=dict(color='red', width=1.5)))

    for cross_type, date in crossovers:
        color = 'green' if cross_type == 'golden' else 'red'
        symbol = 'triangle-up' if cross_type == 'golden' else 'triangle-down'
        fig.add_trace(go.Scatter(x=[date], y=[data.loc[date, 'Low'] if cross_type == 'golden' else data.loc[date, 'High']],
                                 mode='markers',
                                 marker=dict(symbol=symbol, size=15, color=color),
                                 name=f"{cross_type.capitalize()} Cross"))

    fig.update_layout(height=600, width=1000, title_text=f"Stock Analysis for {ticker}")
    fig.update_xaxes(rangeslider_visible=False)
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

def get_explanation_for_crossover(ticker, cross_type, date, company_info, news):
    prompt = f"""As a financial investor, analyze the {cross_type} cross that occurred on {date} for {ticker}. 
    Consider the following company information and news around that time:

    Company Information:
    {company_info}

    Relevant News:
    {news}

    Provide a concise explanation for this stock trend change, focusing on notable events, facts, or company communications that could explain the change. 
    Avoid technical jargon about crossovers and instead focus on fundamental factors that might have influenced investor sentiment or the company's performance.
    Limit your response to 3-4 sentences."""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

st.title("Stock Analysis App")

ticker = st.text_input("Enter a stock ticker:", value="AAPL").upper()

if ticker:
    data = get_stock_data(ticker)
    data = calculate_moving_averages(data)
    crossovers = identify_crossovers(data)
    
    fig = create_candlestick_chart(data, crossovers)
    st.plotly_chart(fig)

    company_info = get_company_info(ticker)
    
    st.subheader("Trend Reversals and Explanations")
    for cross_type, date in crossovers:
        start_date = date - timedelta(days=30)
        end_date = date + timedelta(days=30)
        news = get_company_news(ticker, start_date, end_date)
        
        explanation = get_explanation_for_crossover(ticker, cross_type, date, company_info, news)
        
        st.markdown(f"**{cross_type.capitalize()} Cross on {date.date()}**")
        st.write(explanation)
        st.markdown("---")

st.sidebar.markdown("## About This App")
st.sidebar.write("This app provides stock analysis using technical indicators and AI-generated explanations for trend reversals.")
