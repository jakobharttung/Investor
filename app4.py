import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from anthropic import Anthropic
import json
from bs4 import BeautifulSoup
import numpy as np

# Initialize Anthropic client
anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def serialize_pandas_data(data):
    """Helper function to serialize pandas data structures"""
    if isinstance(data, pd.DataFrame):
        return {
            str(k): serialize_pandas_data(v) 
            for k, v in data.to_dict().items()
        }
    elif isinstance(data, pd.Series):
        return {
            str(k): serialize_pandas_data(v) 
            for k, v in data.to_dict().items()
        }
    elif isinstance(data, dict):
        return {
            str(k): serialize_pandas_data(v) 
            for k, v in data.items()
        }
    elif isinstance(data, (pd.Timestamp, datetime)):
        return data.strftime('%Y-%m-%d')
    elif isinstance(data, (np.int64, np.int32)):
        return int(data)
    elif isinstance(data, (np.float64, np.float32)):
        return float(data)
    elif isinstance(data, list):
        return [serialize_pandas_data(item) for item in data]
    else:
        return data

def get_top_tickers(industry):
    prompt = f"""As a financial investment expert, please provide the stock tickers of the five most promising companies for investment in the {industry} industry. 
    Consider market position, growth potential, and financial stability. 
    Return only the tickers in a comma-separated format."""
    
    message = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = message.content[0].text.strip().split(',')
    return [ticker.strip() for ticker in tickers]

def create_stock_chart(df_dict, period='2y'):
    fig = go.Figure()
    
    for ticker, df in df_dict.items():
        fig.add_trace(
            go.Scatter(x=df.index, y=df['Close'],
                      name=ticker, mode='lines')
        )
    
    fig.update_layout(
        title='Stock Price Comparison',
        yaxis_title='Price',
        xaxis_title='Date',
        height=600
    )
    
    fig.update_layout(xaxis_rangeslider_visible=True)
    
    return fig

def get_stock_recommendation(tickers_data):
    # Prepare a simplified version of the data for the prompt
    simplified_data = {}
    for ticker, data in tickers_data.items():
        simplified_data[ticker] = {
            'financials': serialize_pandas_data(data['financials']),
            'key_stats': {
                'marketCap': data['info'].get('marketCap', 'N/A'),
                'peRatio': data['info'].get('peRatio', 'N/A'),
                'forwardPE': data['info'].get('forwardPE', 'N/A'),
                'dividendYield': data['info'].get('dividendYield', 'N/A'),
            },
            'recent_news': [
                {'title': news.get('title', ''), 'date': news.get('providerPublishTime', '')}
                for news in data['news'][:2]  # Only include 2 most recent news items
            ]
        }

    analysis_prompt = f"""As a financial investment expert, analyze the following companies and recommend the most interesting investment opportunity:
    {json.dumps(simplified_data, indent=2)}
    
    Please provide:
    1. The selected ticker
    2. A brief explanation of why this is the best choice
    3. Key financial metrics supporting the decision"""
    
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240122",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    return message.content[0].text

def create_candlestick_chart(ticker):
    data = yf.download(ticker, period='1y', interval='1d')
    
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
    
    fig.update_layout(
        title=f'{ticker} Price Chart',
        yaxis_title='Price',
        xaxis_title='Date'
    )
    
    return fig, data

def get_technical_analysis(data, ticker):
    # Prepare simplified data for the prompt
    simplified_data = {
        'summary_stats': serialize_pandas_data(data.describe()),
        'recent_prices': serialize_pandas_data(data.tail(5))
    }

    analysis_prompt = f"""As a technical analyst, please identify five key technical patterns in the following stock data for {ticker}.
    Provide the pattern name, date of occurrence, and brief explanation.
    Data summary: {json.dumps(simplified_data, indent=2)}"""
    
    message = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    return message.content[0].text

def main():
    st.title("Investment Analysis App")
    
    industry = st.text_input("Enter industry or sub-industry", value="semiconductors")
    
    if st.button("Analyze"):
        with st.spinner("Analyzing..."):
            try:
                # Get top tickers
                tickers = get_top_tickers(industry)
                st.write(f"Analyzing tickers: {', '.join(tickers)}")
                
                # Fetch historical data
                df_dict = {}
                tickers_data = {}
                
                for ticker in tickers:
                    stock = yf.Ticker(ticker)
                    df_dict[ticker] = stock.history(period='2y', interval='1w')
                    tickers_data[ticker] = {
                        'financials': stock.financials,
                        'info': stock.info,
                        'news': stock.news
                    }
                
                # Display comparison chart
                st.plotly_chart(create_stock_chart(df_dict))
                
                # Get and display recommendation
                recommendation = get_stock_recommendation(tickers_data)
                st.write("### Investment Recommendation")
                st.write(recommendation)
                
                # Get recommended ticker (assuming it's the first word in the recommendation)
                recommended_ticker = recommendation.split()[0].strip()
                
                # Create and display candlestick chart
                candlestick_fig, candlestick_data = create_candlestick_chart(recommended_ticker)
                st.plotly_chart(candlestick_fig)
                
                # Get and display technical analysis
                technical_analysis = get_
