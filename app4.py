import streamlit as st
import yfinance as yf
import anthropic
import os
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_tickers(company):
    prompt = f"As a financial investor, provide the stock ticker for {company} and 5 other tickers for competitors in the same industry of comparable size and strategy. Format the response as a comma-separated list of tickers only."
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    tickers = message.content[0].text.strip().split(',')
    return [ticker.strip() for ticker in tickers]

def get_stock_data(tickers, period='5y'):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        data[ticker] = stock.history(period=period)
    return data

def plot_stock_data(data, period='5y'):
    fig = go.Figure()
    
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=ticker))
    
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
    
    # Sentiment analysis
    sentiment_prompt = f"Analyze the sentiment of the following financial data and news for {ticker}:\n\nFinancials: {financials}\n\nInfo: {info}\n\nNews: {news}\n\nProvide a concise sentiment analysis."
    
    sentiment_message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[
            {"role": "user", "content": sentiment_prompt}
        ]
    )
    
    sentiment = sentiment_message.content[0].text
    
    # Analyst consensus
    consensus_prompt = f"As a financial analyst, provide the current analyst consensus for {ticker} based on available market data and recent performance."
    
    consensus_message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[
            {"role": "user", "content": consensus_prompt}
        ]
    )
    
    consensus = consensus_message.content[0].text
    
    # Overall analysis
    analysis_prompt = f"Provide an overall
