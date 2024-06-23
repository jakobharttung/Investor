import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
import anthropic
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=anthropic_api_key)

def get_related_tickers(company_ticker):
    prompt = f"""As a financial investor, provide 4 stock tickers for companies in the same industry as {company_ticker}. 
    Respond with only the tickers, separated by commas."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return [ticker.strip() for ticker in message.content.split(',')]

def get_stock_data(ticker, period='5y'):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def plot_stock_data(data_dict, period='5y'):
    fig = go.Figure()
    for ticker, data in data_dict.items():
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=ticker))
    
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

def get_sentiment_analysis(ticker, financials, news):
    prompt = f"""As a financial investor, analyze the sentiment for {ticker} based on the following information:
    
    Financials:
    {financials}
    
    Recent News:
    {news}
    
    Provide a sentiment analysis with both qualitative and quantitative aspects."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def get_analyst_consensus(ticker):
    prompt = f"""As a financial investor, provide the analyst consensus for {ticker}. 
    Include both qualitative and quantitative aspects in your response."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def get_industry_analysis(ticker, industry):
    prompt = f"""As a financial investor, analyze {ticker}'s position within the {industry} industry. 
    Provide both qualitative and quantitative insights."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def get_investment_perspective(ticker, historical_data, sentiment, consensus, industry_analysis):
    prompt = f"""As a financial investor, provide an overall perspective on the investment opportunity for {ticker} based on the following information:
    
    Historical Data Summary:
    {historical_data.describe()}
    
    Sentiment Analysis:
    {sentiment}
    
    Analyst Consensus:
    {consensus}
    
    Industry Analysis:
    {industry_analysis}
    
    Provide a comprehensive analysis with both qualitative and quantitative aspects."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def get_investment_recommendation(company, perspectives):
    prompt = f"""As a financial investor, based on the following perspectives for {company} and its industry peers, provide an investment recommendation (Buy, Hold, or Sell) with a short explanation:
    
    {perspectives}
    
    Provide a clear recommendation and a concise explanation."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def get_key_financial_metrics(company, recommendation):
    prompt = f"""As a financial investor, based on the following recommendation for {company}, provide the key financial metrics supporting this recommendation:
    
    {recommendation}
    
    List the most important quantitative metrics that support this recommendation."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

st.title('Investor Analyst App')

company_ticker = st.text_input('Enter a stock ticker to analyze:')

if company_ticker:
    st.write(f"Analyzing {company_ticker}...")
    
    # Get related tickers
    related_tickers = get_related_tickers(company_ticker)
    all_tickers = [company_ticker] + related_tickers
    
    # Get stock data
    stock_data = {ticker: get_stock_data(ticker) for ticker in all_tickers}
    
    # Plot stock data
    st.plotly_chart(plot_stock_data(stock_data))
    
    # Analyze each ticker
    perspectives = {}
    for ticker in all_tickers:
        st.subheader(f"Analysis for {ticker}")
        
        stock = yf.Ticker(ticker)
        financials = stock.financials
        news = stock.news
        
        sentiment = get_sentiment_analysis(ticker, financials, news)
        st.write("Sentiment Analysis:", sentiment)
        
        consensus = get_analyst_consensus(ticker)
        st.write("Analyst Consensus:", consensus)
        
        industry_analysis = get_industry_analysis(ticker, stock.info['industry'])
        st.write("Industry Analysis:", industry_analysis)
        
        perspective = get_investment_perspective(ticker, stock_data[ticker], sentiment, consensus, industry_analysis)
        st.write("Investment Perspective:", perspective)
        
        perspectives[ticker] = perspective
    
    # Get investment recommendation
    recommendation = get_investment_recommendation(company_ticker, perspectives)
    st.subheader("Investment Recommendation")
    st.write(recommendation)
    
    # Get key financial metrics
    key_metrics = get_key_financial_metrics(company_ticker, recommendation)
    st.subheader("Key Financial Metrics")
    st.write(key_metrics)
