import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import pandas as pd
from anthropic import Anthropic
import json

# Initialize Anthropic client
anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def get_competitor_tickers(company_name):
    message = f"""As a financial investor, please provide the stock ticker for {company_name} 
    and 5 other tickers of its main competitors with similar market cap and business strategy. 
    Format the response as a JSON list of tickers only."""
    
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        temperature=0.2,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": message}]
    )
    st.write(response.content)
    tickers = json.loads(response.content[0].text)
    return tickers

def get_stock_data(tickers, period='5y'):
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data[ticker] = stock.history(period=period)
        except:
            st.error(f"Error retrieving data for {ticker}")
    return data

def create_stock_chart(data, period='5y'):
    fig = go.Figure()
    
    for ticker, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'],
                                mode='lines',
                                name=ticker))
    
    fig.update_layout(
        title="Stock Price Comparison",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode='x unified'
    )
    
    # Add range slider and buttons
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True)
        )
    )
    
    return fig

def analyze_company(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    info = stock.info
    news = stock.news
    
    # Sentiment analysis
    sentiment_prompt = f"""As a financial investor, analyze the sentiment of the following company data:
    Financials: {financials.to_dict()}
    Company Info: {info}
    Recent News: {news}
    Provide a clear sentiment score and explanation."""
    
    sentiment_response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        temperature=0.3,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    
    # Analyst consensus
    consensus_prompt = f"As a financial investor, what is the current analyst consensus for {ticker}? Provide specific ratings and price targets."
    
    consensus_response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        temperature=0.2,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    
    return {
        'financials': financials,
        'info': info,
        'sentiment': sentiment_response.content[0].text,
        'consensus': consensus_response.content[0].text
    }

def generate_recommendation(company_name, company_data, competitor_data):
    recommendation_prompt = f"""As a financial investor, based on the following analysis:
    Company: {company_name}
    Company Data: {company_data}
    Competitor Data: {competitor_data}
    
    Provide a clear investment recommendation (Buy/Hold/Sell) with a detailed explanation 
    and key financial metrics supporting the decision."""
    
    recommendation_response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0.3,
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": recommendation_prompt}]
    )
    
    return recommendation_response.content[0].text

# Streamlit app
st.title("Investment Analysis App")

company_name = st.text_input("Enter Company Name:")

if company_name:
    # Get tickers
    tickers = get_competitor_tickers(company_name)
    
    # Get stock data and create chart
    stock_data = get_stock_data(tickers)
    chart = create_stock_chart(stock_data)
    st.plotly_chart(chart)
    
    # Analyze company and competitors
    company_analysis = {}
    for ticker in tickers:
        company_analysis[ticker] = analyze_company(ticker)
    
    # Generate recommendation
    recommendation = generate_recommendation(
        company_name,
        company_analysis[tickers[0]],  # Company analysis
        {t: company_analysis[t] for t in tickers[1:]}  # Competitor analysis
    )
    
    # Display recommendation
    st.subheader("Investment Recommendation")
    st.write(recommendation)
