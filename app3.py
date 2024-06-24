import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import anthropic
import pandas as pd
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_tickers(company):
    prompt = f"As a financial investor, provide the stock ticker for {company} and 5 other tickers for competitors in the same industry, of comparable size and strategy. Respond with just a comma-separated list of tickers."
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip().split(',')

def get_stock_data(tickers, period='5y'):
    data = {}
    st.write(tickers)
    for ticker in tickers:
        st.write(ticker)
        stock = yf.Ticker(ticker)
        data[ticker] = stock.history(period=period)
    return data

def plot_stock_data(data, period='5y'):
    fig = go.Figure()
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=ticker))
    
    fig.update_layout(
        title='Stock Price History',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    
    # Add range slider and buttons
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    return fig

def analyze_ticker(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    info = stock.info
    news = stock.news
    
    # Sentiment analysis
    sentiment_prompt = f"As a financial investor, perform a sentiment analysis on the following data for {ticker}: {financials.to_dict()}, {info}, {news}. Provide a short summary of the sentiment."
    sentiment_response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    sentiment = sentiment_response.content[0].text
    
    # Analyst consensus
    consensus_prompt = f"As a financial investor, provide the analyst consensus for {ticker} based on recent market data and analyst reports. Give a short summary."
    consensus_response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    consensus = consensus_response.content[0].text
    
    # Industry analysis
    industry_prompt = f"As a financial investor, provide an overall analysis of {ticker} within its industry. Consider market position, growth prospects, and competitive advantages. Give a short summary."
    industry_response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": industry_prompt}]
    )
    industry_analysis = industry_response.content[0].text
    
    return {
        'sentiment': sentiment,
        'consensus': consensus,
        'industry_analysis': industry_analysis
    }

def generate_recommendation(company, analyses):
    prompt = f"As a financial investor, based on the following analyses for {company} and its competitors, provide a recommendation (Buy, Hold, or Sell) with a short explanation: {analyses}"
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def get_key_metrics(company, recommendation):
    prompt = f"As a financial investor, based on the recommendation '{recommendation}' for {company}, provide the key financial metrics supporting this recommendation. Give a short, quantitative summary."
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# Streamlit app
st.title('Investor Analyst App')

company = st.text_input('Enter a company name:')

if company:
    tickers = get_tickers(company)
    st.write(tickers)
    stock_data = get_stock_data(tickers)
    
    # Plot stock data
    fig = plot_stock_data(stock_data)
    st.plotly_chart(fig)
    
    # Analyze tickers
    analyses = {}
    for ticker in tickers:
        analyses[ticker] = analyze_ticker(ticker)
    
    # Generate recommendation
    recommendation = generate_recommendation(company, analyses)
    
    # Get key metrics
    key_metrics = get_key_metrics(company, recommendation)
    
    # Display results
    st.subheader('Investment Recommendation')
    st.write(recommendation)
    
    st.subheader('Key Financial Metrics')
    st.write(key_metrics)
