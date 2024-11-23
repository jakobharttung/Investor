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

def serialize_data(obj):
    """Helper function to serialize data for JSON"""
    if isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d')
    return str(obj)

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
    
    # Add range slider
    fig.update_layout(xaxis_rangeslider_visible=True)
    
    return fig

def get_stock_recommendation(tickers_data):
    # Prepare data for prompt by serializing it properly
    serialized_data = {}
    for ticker, data in tickers_data.items():
        serialized_data[ticker] = {
            'financials': {
                k: serialize_data(v) for k, v in data['financials'].items()
            },
            'info': {
                k: serialize_data(v) for k, v in data['info'].items()
                if k not in ['longBusinessSummary']  # Exclude long text fields
            },
            'news': [
                {k: serialize_data(v) for k, v in news_item.items()}
                for news_item in data['news'][:3]  # Limit to 3 news items
            ]
        }

    analysis_prompt = f"""As a financial investment expert, analyze the following companies and recommend the most interesting investment opportunity:
    {json.dumps(serialized_data, indent=2)}
    
    Please provide:
    1. The selected ticker
    2. A brief explanation of why this is the best choice
    3. Key financial metrics supporting the decision"""
    
    message = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
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
    # Prepare data for prompt by serializing it
    serialized_data = {
        'summary': {
            k: serialize_data(v) for k, v in data.describe().to_dict().items()
        },
        'recent_data': data.tail(30).to_dict()  # Include last 30 days of data
    }

    analysis_prompt = f"""As a technical analyst, please identify five key technical patterns in the following stock data for {ticker}.
    Provide the pattern name, date of occurrence, and brief explanation.
    Data summary: {json.dumps(serialized_data, indent=2)}"""
    
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240122",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    return message.content[0].text

def main():
    st.title("Investment Analysis App")
    
    # Industry input
    industry = st.text_input("Enter industry or sub-industry", value="semiconductors")
    
    if st.button("Analyze"):
        with st.spinner("Analyzing..."):
            try:
                # Get top tickers
                tickers = get_top_tickers(industry)
                
                # Fetch historical data
                df_dict = {}
                tickers_data = {}
                
                for ticker in tickers:
                    stock = yf.Ticker(ticker)
                    df_dict[ticker] = stock.history(period='2y', interval='1wk')
                    tickers_data[ticker] = {
                        'financials': stock.financials.to_dict(),
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
                recommended_ticker = recommendation.split()[0]
                
                # Create and display candlestick chart
                candlestick_fig, candlestick_data = create_candlestick_chart(recommended_ticker)
                st.plotly_chart(candlestick_fig)
                
                # Get and display technical analysis
                technical_analysis = get_technical_analysis(candlestick_data, recommended_ticker)
                st.write("### Technical Analysis")
                st.write(technical_analysis)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
