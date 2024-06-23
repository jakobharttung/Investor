import streamlit as st
import yfinance as yf
import anthropic
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_related_tickers(company):
    prompt = f"As a financial investor, provide 3 stock tickers for companies in the same industry as {company}. Respond with only the tickers separated by commas."
    message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=100,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip().split(',')

def get_stock_data(ticker, period='5y'):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def plot_stock_data(data_dict):
    fig = go.Figure()
    for ticker, data in data_dict.items():
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=ticker))
    fig.update_layout(title='Stock Price Comparison', xaxis_title='Date', yaxis_title='Price')
    return fig

def analyze_ticker(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials.to_dict()
    news = stock.news

    # Sentiment analysis
    sentiment_prompt = f"As a financial investor, analyze the sentiment of the following financial data and news for {ticker}: {financials}, {news}. Provide a short sentiment analysis in a few lines."
    sentiment_message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    sentiment = sentiment_message.content[0].text

    # Analyst consensus
    consensus_prompt = f"As a financial investor, provide the analyst consensus for {ticker} based on recent market data and analyst reports. Give a short answer in a few lines."
    consensus_message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    consensus = consensus_message.content[0].text

    # Industry analysis
    industry_prompt = f"As a financial investor, provide an overall analysis of {ticker} within its industry. Give a short answer in a few lines."
    industry_message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": industry_prompt}]
    )
    industry_analysis = industry_message.content[0].text

    return {
        'sentiment': sentiment,
        'consensus': consensus,
        'industry_analysis': industry_analysis
    }

def get_recommendation(company, analyses):
    prompt = f"As a financial investor, based on the following analyses for {company} and related companies, provide a recommendation (Buy, Hold, or Sell) with a short explanation: {analyses}"
    message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def get_key_metrics(company, recommendation):
    prompt = f"As a financial investor, provide the key financial metrics supporting the {recommendation} recommendation for {company}. Give a short answer with quantitative and qualitative outputs in a few lines."
    message = client.messages.create(
        model="claude-3-sonnet-20240620",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

st.title('Investor Analyst App')

company = st.text_input('Enter a stock ticker:')

if company:
    related_tickers = get_related_tickers(company)
    all_tickers = [company] + related_tickers

    data_dict = {ticker: get_stock_data(ticker) for ticker in all_tickers}

    st.subheader('Stock Price Comparison')
    period = st.select_slider('Select period', options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'])
    fig = plot_stock_data({ticker: get_stock_data(ticker, period) for ticker in all_tickers})
    st.plotly_chart(fig)

    analyses = {ticker: analyze_ticker(ticker) for ticker in all_tickers}
    recommendation = get_recommendation(company, analyses)
    key_metrics = get_key_metrics(company, recommendation)

    st.subheader('Investment Recommendation')
    st.write(recommendation)

    st.subheader('Key Financial Metrics')
    st.write(key_metrics)
