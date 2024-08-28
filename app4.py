import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from anthropic import Anthropic
import os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_tickers(company):
    prompt = f"""As a financial investor, provide a list of stock tickers for {company} and 5 other competitors in the same industry with comparable size and strategy. Format the response as a comma-separated list of tickers only."""
    
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = response.content[0].text.strip().split(',')
    return [ticker.strip() for ticker in tickers]

def get_stock_data(tickers, period='5y'):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        data[ticker] = hist[['Open', 'High', 'Low', 'Close']]
    return data

def plot_stock_data(data, period='5y'):
    fig = go.Figure()
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=ticker, mode='lines'))
    
    fig.update_layout(
        title='Stock Price Comparison',
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
    
    # Prepare data for sentiment analysis
    financial_summary = financials.to_json()
    info_summary = str(info)
    news_summary = str(news)
    
    # Sentiment analysis
    sentiment_prompt = f"""As a financial investor, analyze the sentiment for {ticker} based on the following data:
    Financials: {financial_summary}
    Info: {info_summary}
    News: {news_summary}
    Provide a brief sentiment analysis focusing on key factors affecting the stock."""
    
    sentiment_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    
    sentiment = sentiment_response.content[0].text.strip()
    
    # Analyst consensus
    consensus_prompt = f"""As a financial investor, provide the analyst consensus for {ticker} based on available data and market trends. Include any relevant ratings or price targets."""
    
    consensus_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    
    consensus = consensus_response.content[0].text.strip()
    
    # Overall analysis
    analysis_prompt = f"""As a financial investor, provide an overall analysis of {ticker} within its industry. Include key financial metrics, growth prospects, and competitive position. Provide specific numbers where relevant."""
    
    analysis_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    analysis = analysis_response.content[0].text.strip()
    
    return {
        'sentiment': sentiment,
        'consensus': consensus,
        'analysis': analysis
    }

def generate_recommendation(company, analyses):
    prompt = f"""As a financial investor, based on the following analyses for {company} and its competitors, provide an investment recommendation (Buy, Hold, or Sell) with a brief explanation:

    {analyses}

    Format the response as:
    Recommendation: [Buy/Hold/Sell]
    Explanation: [Your explanation here]
    """
    
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()

def get_key_metrics(company, recommendation):
    prompt = f"""As a financial investor, based on the following recommendation for {company}, provide the key financial metrics supporting this recommendation:

    {recommendation}

    List 3-5 specific quantitative metrics with their values and a brief explanation of their significance."""
    
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()

# Streamlit app
st.title("Investor Analysis App")

company = st.text_input("Enter a company name:")

if company:
    with st.spinner("Analyzing..."):
        tickers = get_tickers(company)
        stock_data = get_stock_data(tickers)
        
        st.subheader("Stock Price Comparison")
        fig = plot_stock_data(stock_data)
        st.plotly_chart(fig)
        
        analyses = {}
        for ticker in tickers:
            analyses[ticker] = analyze_ticker(ticker)
        
        recommendation = generate_recommendation(company, str(analyses))
        key_metrics = get_key_metrics(company, recommendation)
        
        st.subheader("Investment Recommendation")
        st.write(recommendation)
        
        st.subheader("Key Financial Metrics")
        st.write(key_metrics)
