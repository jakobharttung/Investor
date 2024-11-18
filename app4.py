import streamlit as st
import yfinance as yf
import anthropic
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=st.secrets["ANTHROPIC_API_KEY"]
)

def get_competitor_tickers(company_name):
    prompt = f"""As a financial investor, please provide the stock ticker for {company_name} and 5 other tickers 
    for its main competitors in the same industry with similar market cap and business strategy. 
    Format the response as a comma-separated list of tickers only."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20240122",
        max_tokens=300,
        temperature=0.2,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = message.content.strip().split(',')
    return [ticker.strip() for ticker in tickers]

def get_stock_data(tickers, period='5y'):
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data[ticker] = stock.history(period=period)
        except:
            st.error(f"Error retrieving data for {ticker}")
    return data

def create_stock_chart(data, period='5y'):
    fig = go.Figure()
    
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            name=ticker,
            mode='lines'
        ))
    
    fig.update_layout(
        title='Stock Price Comparison',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    
    # Add range slider and buttons
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True)
        )
    )
    
    return fig

def analyze_company(ticker):
    stock = yf.Ticker(ticker)
    
    # Gather data
    financials = stock.financials
    info = stock.info
    news = stock.news
    
    # Sentiment analysis
    sentiment_prompt = f"""As a financial investor, analyze the sentiment of the following company data:
    Financials: {financials.to_dict()}
    Company Info: {info}
    Recent News: {news}
    Provide a clear sentiment analysis with specific metrics and trends."""
    
    sentiment = client.messages.create(
        model="claude-3-5-sonnet-20240122",
        max_tokens=500,
        temperature=0.3,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    
    # Analyst consensus
    consensus_prompt = f"As a financial investor, what is the current analyst consensus for {ticker} based on the provided data?"
    
    consensus = client.messages.create(
        model="claude-3-5-sonnet-20240122",
        max_tokens=300,
        temperature=0.2,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    
    return {
        'financials': financials,
        'info': info,
        'sentiment': sentiment.content,
        'consensus': consensus.content
    }

def generate_recommendation(company_analysis, competitor_analyses):
    prompt = f"""As a financial investor, based on the following analyses:
    
    Target Company ({company_analysis['ticker']}):
    {company_analysis['data']}
    
    Competitors:
    {competitor_analyses}
    
    Provide a clear Buy, Hold, or Sell recommendation for {company_analysis['ticker']} with a detailed explanation 
    and key supporting metrics."""
    
    recommendation = client.messages.create(
        model="claude-3-5-sonnet-20240122",
        max_tokens=800,
        temperature=0.3,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return recommendation.content

# Streamlit UI
st.title("Investment Analysis App")

company_name = st.text_input("Enter Company Name:")

if company_name:
    # Get tickers
    tickers = get_competitor_tickers(company_name)
    
    # Get stock data
    stock_data = get_stock_data(tickers)
    
    # Display stock chart
    chart = create_stock_chart(stock_data)
    st.plotly_chart(chart)
    
    # Analyze companies
    analyses = {}
    for ticker in tickers:
        analyses[ticker] = analyze_company(ticker)
    
    # Generate recommendation
    company_ticker = tickers[0]  # Assuming first ticker is the target company
    recommendation = generate_recommendation(
        {'ticker': company_ticker, 'data': analyses[company_ticker]},
        {ticker: data for ticker, data in analyses.items() if ticker != company_ticker}
    )
    
    # Display recommendation
    st.subheader("Investment Recommendation")
    st.write(recommendation)
