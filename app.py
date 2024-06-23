import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from openai import OpenAI
from bs4 import BeautifulSoup
import os
import requests

# Initialize OpenAI client
client = OpenAI(
  api_key='sk-proj-IHp8yddYHl6QMILsVtChT3BlbkFJBrkg83EFMbeVkEKNkfK4'
)

# Helper function to call OpenAI API
def call_openai(prompt, max_tokens=100):
    chat_completion = completion = openai.chat.completions.create(
      model="gpt-4",
      messages=[
        {
            "role": "user",
            "content": f"{prompt}",
        },
    ],
)
# Helper function to get similar companies
def get_similar_companies(ticker):
    prompt = f"Given the stock ticker {ticker}, list four other companies in the same industry."
    response = call_openai(prompt, max_tokens=50)
    return response.split(',')

# Helper function to get stock data
def get_stock_data(ticker, period='5y'):
    stock = yf.Ticker(ticker)
    return stock.history(period=period)

# Helper function to get financials and news sentiment analysis
def get_sentiment_and_analysis(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials.to_dict()
    news_url = f"https://finance.yahoo.com/quote/{ticker}/news?p={ticker}"
    news_response = requests.get(news_url)
    soup = BeautifulSoup(news_response.content, 'html.parser')
    headlines = [item.get_text() for item in soup.find_all('h3')]

    prompt = f"Analyze the following financial data and news headlines for sentiment and provide an overall analysis:\n\nFinancials: {financials}\n\nHeadlines: {headlines}"
    response = call_openai(prompt, max_tokens=300)
    return response

# Helper function to get investment recommendation
def get_investment_recommendation(ticker, analysis_data):
    prompt = f"Based on the following analysis data:\n\n{analysis_data}\n\nProvide an investment recommendation for the company with the stock ticker {ticker} (Buy, Hold, or Sell) with a short explanation."
    response = call_openai(prompt, max_tokens=100)
    return response

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

