import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from anthropic import Anthropic, Client
import os

# Initialize Anthropic client
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', 'YOUR_ANTHROPIC_API_KEY')
anthropic_client = Client(api_key=anthropic_api_key)

# Helper function to get similar companies
def get_similar_companies(ticker):
    prompt = f"Given the stock ticker {ticker}, list four other companies in the same industry."
    response = anthropic_client.completions.create(
        model="claude-v1",
        prompt=prompt,
        max_tokens_to_sample=50,
        stop_sequences=["\n"]
    )
    return response['completion'].strip().split(',')

# Helper function to get stock data
def get_stock_data(ticker, period='5y'):
    stock = yf.Ticker(ticker)
    return stock.history(period=period)

# Helper function to get financials and news sentiment analysis
def get_sentiment_and_analysis(ticker):
    prompt = f"Given the financials and recent news of the company with the stock ticker {ticker}, provide a sentiment analysis, an analyst consensus, an industry analysis, and an overall investment perspective."
    response = anthropic_client.completions.create(
        model="claude-v1",
        prompt=prompt,
        max_tokens_to_sample=300,
        stop_sequences=["\n"]
    )
    return response['completion'].strip()

# Helper function to get investment recommendation
def get_investment_recommendation(ticker, analysis_data):
    prompt = f"Based on the following analysis data:\n\n{analysis_data}\n\nProvide an investment recommendation for the company with the stock ticker {ticker} (Buy, Hold, or Sell) with a short explanation."
    response = anthropic_client.completions.create(
        model="claude-v1",
        prompt=prompt,
        max_tokens_to_sample=100,
        stop_sequences=["\n"]
    )
    return response['completion'].strip()

# Streamlit app
st.title('Investor Analyst App')

# Input for company ticker
company_ticker = st.text_input('Enter a stock ticker for the company you want to analyze:', 'AAPL')

if company_ticker:
    st.subheader(f'Analyzing {company_ticker}')
    
    # Get similar companies
    st.write("Fetching similar companies...")
    similar_companies = get_similar_companies(company_ticker)
    st.write(f"Similar companies: {', '.join(similar_companies)}")

    # Get historical data
    st.write("Fetching historical data...")
    tickers = [company_ticker] + similar_companies
    data = {ticker: get_stock_data(ticker) for ticker in tickers}
    
    # Plot historical data
    st.write("Plotting historical data...")
    fig = go.Figure()
    for ticker in tickers:
        fig.add_trace(go.Scatter(x=data[ticker].index, y=data[ticker]['Close'], mode='lines', name=ticker))
    
    fig.update_layout(title='Stock Prices Over Time', xaxis_title='Date', yaxis_title='Stock Price (USD)',)
    st.plotly_chart(fig)
    
    # Analyze each ticker
    analysis_data = {}
    for ticker in tickers:
        st.write(f"Analyzing {ticker}...")
        sentiment_analysis = get_sentiment_and_analysis(ticker)
        st.write(f"Sentiment Analysis for {ticker}: {sentiment_analysis}")
        analysis_data[ticker] = sentiment_analysis

    # Get investment recommendation
    st.write("Fetching investment recommendation...")
    recommendation = get_investment_recommendation(company_ticker, analysis_data)
    st.write(f"Investment Recommendation for {company_ticker}: {recommendation}")

    # Summary
    st.subheader('Summary Recommendation')
    st.write(recommendation)
    st.write("Key Financial Metrics:")
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        st.write(f"{ticker} - Market Cap: {stock.info['marketCap']}, P/E Ratio: {stock.info['trailingPE']}, EPS: {stock.info['trailingEps']}, Dividend Yield: {stock.info['dividendYield']}")
