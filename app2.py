import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from anthropic import Anthropic
import pandas as pd

# Initialize Anthropic client
anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def get_stock_data(ticker, period="5y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def get_company_info(company_name):
    prompt = f"""As a financial investor, provide the stock ticker for {company_name} and 3 other tickers for its main competitors in the same industry. Format the response as a Python list of strings, with the first element being the ticker for {company_name}."""
    
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=150,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = eval(response.content[0].text)
    return tickers

def analyze_ticker(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    news = stock.news
    
    # Sentiment analysis
    sentiment_prompt = f"Analyze the sentiment of the following financial data and news for {ticker}:\n\nFinancials:\n{financials}\n\nNews:\n{news}\n\nProvide a brief sentiment analysis."
    sentiment_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    sentiment = sentiment_response.content[0].text

    # Analyst consensus
    consensus_prompt = f"What is the current analyst consensus for {ticker}? Provide a brief summary."
    consensus_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=150,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    consensus = consensus_response.content[0].text

    # Industry analysis
    industry_prompt = f"Analyze {ticker} within its industry. Provide a brief overview of its position and performance relative to competitors."
    industry_response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=200,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": industry_prompt}]
    )
    industry_analysis = industry_response.content[0].text

    return {
        "sentiment": sentiment,
        "consensus": consensus,
        "industry_analysis": industry_analysis
    }

def generate_recommendation(company, analyses):
    prompt = f"""As a financial investor, based on the following analyses for {company} and its competitors, provide a recommendation (Buy, Hold, or Sell) with a brief explanation:

{analyses}

Format your response as a Python dictionary with keys 'recommendation' and 'explanation'."""

    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=250,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    st.write(response.content[0].text)
    recommendation = eval(response.content[0].text)
    return recommendation

def get_key_metrics(company, recommendation):
    prompt = f"""As a financial investor, provide the key financial metrics supporting the following recommendation for {company}:

{recommendation}

List 3-5 quantitative metrics with their values and a brief qualitative explanation for each."""

    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    metrics = response.content[0].text
    return metrics

st.title("Investor Analyst App")

company = st.text_input("Enter a company name:")

if company:
    tickers = get_company_info(company)
    
    # Retrieve historical data
    data = {ticker: get_stock_data(ticker) for ticker in tickers}
    
    # Create plotly chart
    fig = go.Figure()
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=ticker))
    
    fig.update_layout(
        title=f"{company} and Competitors Stock Prices",
        xaxis_title="Date",
        yaxis_title="Price",
        legend_title="Tickers"
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
    
    st.plotly_chart(fig)
    
    # Analyze tickers
    analyses = {ticker: analyze_ticker(ticker) for ticker in tickers}
    
    # Generate recommendation
    recommendation = generate_recommendation(company, analyses)
    
    # Display recommendation
    st.subheader("Investment Recommendation")
    st.write(f"**{recommendation['recommendation']}**")
    st.write(recommendation['explanation'])
    
    # Display key metrics
    st.subheader("Key Financial Metrics")
    metrics = get_key_metrics(company, recommendation)
    st.write(metrics)
