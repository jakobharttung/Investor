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

def get_related_tickers(company):
    prompt = f"""
    As a financial investor, please provide 4 stock tickers for companies in the same industry as {company}.
    Give only the tickers, separated by commas.
    """
    response = client.completions.create(
        model="claude-2",
        prompt=prompt,
        max_tokens_to_sample=100
    )
    return [ticker.strip() for ticker in response.completion.split(',')]

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
        title='Stock Price History',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    
    # Add range slider and selector
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

def analyze_ticker(ticker, financials, news):
    prompt = f"""
    As a financial investor, please provide:
    1. A sentiment analysis based on the following financial data and news for {ticker}:
    Financial data: {financials}
    News: {news}
    
    2. An analyst consensus on {ticker}.
    
    3. An overall analysis of {ticker} within its industry.
    
    4. An overall perspective on the investment opportunity for {ticker}, considering the historical market data, financials, and news.
    
    Please provide both quantitative and qualitative outputs where applicable.
    """
    response = client.completions.create(
        model="claude-2",
        prompt=prompt,
        max_tokens_to_sample=1000
    )
    return response.completion

def generate_recommendation(company, analyses):
    prompt = f"""
    As a financial investor, based on the following analyses of {company} and its competitors:
    {analyses}
    
    Please provide an investment recommendation for {company}: Buy, Hold, or Sell.
    Include a short explanation for your recommendation.
    Also, list the key financial metrics supporting this recommendation.
    """
    response = client.completions.create(
        model="claude-2",
        prompt=prompt,
        max_tokens_to_sample=500
    )
    return response.completion

st.title('Investor Analyst App')

company = st.text_input('Enter a stock ticker:')

if company:
    related_tickers = get_related_tickers(company)
    all_tickers = [company] + related_tickers
    
    stock_data = get_stock_data(all_tickers)
    
    st.plotly_chart(plot_stock_data(stock_data))
    
    analyses = {}
    for ticker in all_tickers:
        stock = yf.Ticker(ticker)
        financials = stock.financials.to_dict()
        news = stock.news
        
        analysis = analyze_ticker(ticker, financials, news)
        analyses[ticker] = analysis
        
        st.subheader(f"Analysis for {ticker}")
        st.write(analysis)
    
    recommendation = generate_recommendation(company, analyses)
    
    st.subheader("Investment Recommendation")
    st.write(recommendation)
