import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import requests
import anthropic
import os

os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]         
my_api_key = st.secrets['ANTHROPIC_API_KEY']  

# Initialize the language model (pseudo code, replace with actual API calls)
def initialize_language_model():
    # Replace with actual initialization code for the language model
    return anthropic.Client(api_key="your_api_key")

language_model = initialize_language_model()

# Function to call the language model
def call_language_model(prompt):
    # Replace with actual API call to the language model
    response = language_model.completion(
        prompt=prompt,
        max_tokens=150
    )
    return response['choices'][0]['text'].strip()

# Function to retrieve stock tickers in the same industry
def get_related_tickers(company_ticker):
    prompt = f"Given the stock ticker {company_ticker}, provide 4 other tickers of companies in the same industry."
    return call_language_model(prompt).split()

# Function to retrieve and process stock data
def get_stock_data(tickers):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        data[ticker] = stock.history(period='5y')
    return data

# Function to retrieve financials and news for sentiment analysis
def get_financials_and_news(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    news = stock.news
    return financials, news

# Function to perform sentiment analysis
def perform_sentiment_analysis(financials, news):
    prompt = f"Perform a sentiment analysis based on the following financial data and news:\nFinancials: {financials}\nNews: {news}"
    return call_language_model(prompt)

# Function to retrieve analyst consensus
def get_analyst_consensus(ticker):
    prompt = f"Retrieve the analyst consensus for the stock ticker {ticker}."
    return call_language_model(prompt)

# Function to retrieve overall analysis
def get_overall_analysis(ticker, industry_data):
    prompt = f"Provide an overall analysis of the stock ticker {ticker} within its industry context. Industry data: {industry_data}"
    return call_language_model(prompt)

# Function to generate investment perspective
def get_investment_perspective(ticker, historical_data, sentiment, consensus, analysis):
    prompt = f"Based on the historical market data, sentiment analysis, analyst consensus, and overall analysis, generate an investment perspective for the stock ticker {ticker}."
    return call_language_model(prompt)

# Streamlit app layout
st.title('Investor Analyst App')
company_ticker = st.text_input('Enter the stock ticker for the Company you want to analyze:', 'AAPL')

if company_ticker:
    st.write(f'Analyzing {company_ticker} and related companies...')

    related_tickers = get_related_tickers(company_ticker)
    tickers = [company_ticker] + related_tickers

    st.write('Retrieved related tickers:', ', '.join(tickers))

    stock_data = get_stock_data(tickers)

    # Plotly visualization
    fig = go.Figure()

    for ticker in tickers:
        fig.add_trace(go.Scatter(
            x=stock_data[ticker].index,
            y=stock_data[ticker]['Close'],
            mode='lines',
            name=ticker
        ))

    fig.update_layout(
        title='Stock Prices Over the Last 5 Years',
        xaxis_title='Date',
        yaxis_title='Close Price',
        updatemenus=[dict(
            type="buttons",
            direction="left",
            buttons=list([
                dict(count=1,
                     label="1Y",
                     step="year",
                     stepmode="backward"),
                dict(count=3,
                     label="3Y",
                     step="year",
                     stepmode="backward"),
                dict(count=5,
                     label="5Y",
                     step="year",
                     stepmode="backward"),
                dict(step="all",
                     label="All")
            ]),
        )]
    )

    st.plotly_chart(fig)

    overall_perspectives = []
    for ticker in tickers:
        financials, news = get_financials_and_news(ticker)
        sentiment = perform_sentiment_analysis(financials, news)
        consensus = get_analyst_consensus(ticker)
        analysis = get_overall_analysis(ticker, stock_data)
        perspective = get_investment_perspective(ticker, stock_data[ticker], sentiment, consensus, analysis)
        overall_perspectives.append(perspective)

    prompt = f"Based on the following perspectives, provide a recommendation (Buy, Hold, Sell) with a short explanation for the stock ticker {company_ticker}: {overall_perspectives}"
    recommendation = call_language_model(prompt)

    st.write('Investment Recommendation:')
    st.write(recommendation)
