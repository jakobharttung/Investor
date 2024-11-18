import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import anthropic
import os
from bs4 import BeautifulSoup
import pandas as pd
import requests

# Initialize Anthropic client
client = anthropic.Client(api_key=st.secrets["ANTHROPIC_API_KEY"])

def get_competitor_tickers(company_name):
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{
            "role": "user",
            "content": f"As a financial analyst, provide the stock ticker for {company_name} and 5 main competitors of similar size and strategy in the same industry. Format response as comma-separated tickers only."
        }]
    )
    tickers = message.content[0].text.strip().split(',')
    return [ticker.strip() for ticker in tickers]

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
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            name=ticker,
            mode='lines'
        ))
    
    fig.update_layout(
        title='Stock Price Comparison',
        xaxis_title='Date',
        yaxis_title='Price',
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
    
    # Gather data
    financials = stock.financials
    info = stock.info
    news = stock.news
    
    # Sentiment analysis
    sentiment_prompt = f"As a financial analyst, analyze the sentiment of recent news and financial data for {ticker}. Consider market perception and momentum."
    sentiment = client.messages.create(
        model="claude-3-sonnet-20240229",
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": sentiment_prompt}]
    )
    
    # Analyst consensus
    consensus_prompt = f"As a financial analyst, provide the current analyst consensus for {ticker} based on available financial data and market conditions."
    consensus = client.messages.create(
        model="claude-3-sonnet-20240229",
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": consensus_prompt}]
    )
    
    # Overall analysis
    analysis_prompt = f"As a financial analyst, provide a detailed analysis of {ticker}'s financial performance and position within its industry, including key metrics and comparisons."
    analysis = client.messages.create(
        model="claude-3-sonnet-20240229",
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    return {
        'sentiment': sentiment.content[0].text,
        'consensus': consensus.content[0].text,
        'analysis': analysis.content[0].text
    }

def generate_recommendation(company, analyses):
    recommendation_prompt = f"""As a financial investor, based on the following analyses, provide a clear Buy, Hold, or Sell recommendation for {company} with a brief explanation:
    
    {analyses}
    
    Format: [RECOMMENDATION]: explanation"""
    
    recommendation = client.messages.create(
        model="claude-3-sonnet-20240229",
        system="You are a financial investor, respond with facts and focused messages",
        messages=[{"role": "user", "content": recommendation_prompt}]
    )
    
    return recommendation.content[0].text

def main():
    st.title("Investment Analysis App")
    
    company = st.text_input("Enter company name:")
    
    if company:
        with st.spinner("Analyzing..."):
            # Get tickers
            tickers = get_competitor_tickers(company)
            
            # Get stock data and create chart
            stock_data = get_stock_data(tickers)
            chart = create_stock_chart(stock_data)
            st.plotly_chart(chart)
            
            # Analyze each company
            analyses = {}
            for ticker in tickers:
                analyses[ticker] = analyze_company(ticker)
            
            # Generate recommendation
            recommendation = generate_recommendation(company, analyses)
            
            # Display results
            st.header("Investment Recommendation")
            st.write(recommendation)
            
            # Get key metrics
            metrics_prompt = f"As a financial analyst, list the key financial metrics supporting the recommendation for {company}."
            metrics = client.messages.create(
                model="claude-3-sonnet-20240229",
                system="You are a financial investor, respond with facts and focused messages",
                messages=[{"role": "user", "content": metrics_prompt}]
            )
            
            st.header("Key Supporting Metrics")
            st.write(metrics.content[0].text)

if __name__ == "__main__":
    main()
