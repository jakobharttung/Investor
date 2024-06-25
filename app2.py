import streamlit as st
import yfinance as yf
import anthropic
import os
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def get_tickers(company):
    prompt = f"As a financial investor, provide the stock ticker for {company} and 5 other tickers for competitors in the same industry of comparable size and strategy. Format the response as a comma-separated list of tickers only."
    
    response = client.messages.create(
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
        data[ticker] = stock.history(period=period)
    return data

def plot_stock_data(data, period='5y'):
    fig = go.Figure()
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=ticker))
    
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
    sentiment_prompt = f"As a financial investor, analyze the sentiment of the following financial data and news for {ticker}:\n\nFinancials: {financials}\n\nInfo: {info}\n\nNews: {news}\n\nProvide a concise sentiment analysis."
    sentiment_response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    sentiment = sentiment_response.content[0].text.strip()
    
    # Analyst consensus
    consensus_prompt = f"As a financial investor, provide the analyst consensus for {ticker} based on available data."
    consensus_response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    consensus = consensus_response.content[0].text.strip()
    
    # Overall analysis
    analysis_prompt = f"As a financial investor, provide an overall analysis and detailed financial numbers for {ticker} within its industry."
    analysis_response = client.messages.create(
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
    prompt = f"As a financial investor, based on the following analyses for {company} and its competitors, provide a recommendation (Buy, Hold, or Sell) with a short explanation:\n\n"
    for ticker, analysis in analyses.items():
        prompt += f"{ticker}:\nSentiment: {analysis['sentiment']}\nConsensus: {analysis['consensus']}\nAnalysis: {analysis['analysis']}\n\n"
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        system="You are a financial investor, respond with facts and focused messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()

def get_key_metrics(company, recommendation):
    prompt = f"As a financial investor, based on the following recommendation for {company}, provide the key financial metrics supporting it:\n\n{recommendation}"
    
    response = client.messages.create(
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
    tickers = get_tickers(company)
    stock_data = get_stock_data(tickers)
    
    st.plotly_chart(plot_stock_data(stock_data))
    
    analyses = {}
    for ticker in tickers:
        analyses[ticker] = analyze_ticker(ticker)
    
    recommendation = generate_recommendation(company, analyses)
    key_metrics = get_key_metrics(company, recommendation)
    
    st.subheader("Investment Recommendation")
    st.write(recommendation)
    
    st.subheader("Key Financial Metrics")
    st.write(key_metrics)
