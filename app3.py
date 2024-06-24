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

def get_stock_data(ticker, period="5y"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    return hist

def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

def get_company_news(ticker):
    stock = yf.Ticker(ticker)
    return stock.news

def get_company_financials(ticker):
    stock = yf.Ticker(ticker)
    return stock.financials

def call_anthropic(prompt):
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

st.title("Investor Analyst App")

company = st.text_input("Enter a company name:")

if company:
    # Get stock ticker and competitors
    prompt = f"What is the stock ticker for {company}? Also, provide a Python list of 5 other tickers for competitors in the same industry as {company} with comparable size and strategy."
    response = call_anthropic(prompt)
    
    # Parse the response to get the main ticker and competitor tickers
    lines = response.split('\n')
    main_ticker = lines[0].split(':')[-1].strip()
    competitor_tickers = eval(lines[1])
    
    all_tickers = [main_ticker] + competitor_tickers
    
    # Get historical data for all tickers
    data = {ticker: get_stock_data(ticker) for ticker in all_tickers}
    
    # Create plotly chart
    fig = go.Figure()
    for ticker, hist in data.items():
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name=ticker))
    
    fig.update_layout(title='Stock Price History', xaxis_title='Date', yaxis_title='Price')
    
    # Add period selection buttons
    periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
    buttons = []
    for period in periods:
        buttons.append(dict(label=period, method='update', args=[{'visible': [True]*len(all_tickers)}, {'xaxis': {'range': [datetime.now() - timedelta(days={'mo': 30, 'y': 365}[period[-1]]*int(period[:-1])), datetime.now()]}}]))
    
    fig.update_layout(updatemenus=[dict(type='buttons', showactive=False, buttons=buttons)])
    
    st.plotly_chart(fig)
    
    # Analyze each ticker
    analyses = {}
    for ticker in all_tickers:
        info = get_company_info(ticker)
        news = get_company_news(ticker)
        financials = get_company_financials(ticker)
        
        # Sentiment analysis
        prompt = f"Perform a sentiment analysis on this data for {ticker}: {info}\n{news}\n{financials}"
        sentiment = call_anthropic(prompt)
        
        # Analyst consensus
        prompt = f"What is the analyst consensus for {ticker}?"
        consensus = call_anthropic(prompt)
        
        # Overall analysis
        prompt = f"Provide an overall analysis of {ticker} within its industry."
        overall = call_anthropic(prompt)
        
        analyses[ticker] = {
            'sentiment': sentiment,
            'consensus': consensus,
            'overall': overall
        }
    
    # Generate recommendation
    prompt = f"Based on the following analyses, generate a recommendation (Buy, Hold, or Sell) for investing in {company} compared to its competitors. Provide a short explanation for the recommendation.\n\n{analyses}"
    recommendation = call_anthropic(prompt)
    
    # Display recommendation
    st.subheader("Investment Recommendation")
    st.write(recommendation)
    
    # Generate and display key financial metrics
    prompt = f"Based on the recommendation and analyses, what are the key financial metrics supporting this recommendation for {company}? Provide a concise summary."
    metrics = call_anthropic(prompt)
    
    st.subheader("Key Financial Metrics")
    st.write(metrics)
