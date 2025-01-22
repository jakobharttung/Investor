import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from anthropic import Anthropic
import json
import numpy as np

# Initialize Anthropic client
anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def serialize_timestamp(obj):
    """Convert timestamp objects to string format"""
    if isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, (np.int64, np.float64)):
        return str(obj)
    elif isinstance(obj, dict):
        return {str(k): serialize_timestamp(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_timestamp(item) for item in obj]
    return obj

def get_top_tickers(industry):
    prompt = f"""As a financial investment expert, please provide the stock tickers of the five most promising companies for investment in the {industry} industry. 
    Return only the tickers in a comma-separated format."""
    
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240122",
        max_tokens=1000,
        system="You are a financial investor",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = message.content[0].text.strip().split(',')
    return [ticker.strip() for ticker in tickers]

def create_stock_chart(df_dict):
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
        height=600,
        xaxis_rangeslider_visible=True
    )
    
    return fig

def get_stock_recommendation(tickers_data):
    # Prepare a simplified version of the data for the prompt
    simplified_data = {}
    for ticker, data in tickers_data.items():
        simplified_data[ticker] = {
            'current_price': data['info'].get('currentPrice', 'N/A'),
            'market_cap': data['info'].get('marketCap', 'N/A'),
            'sector': data['info'].get('sector', 'N/A'),
            'industry': data['info'].get('industry', 'N/A')
        }
    
    analysis_prompt = f"""As a financial investment expert, analyze these companies and recommend the best investment:
    {json.dumps(simplified_data, indent=2)}
    
    Provide:
    1. The selected ticker
    2. Brief explanation why
    3. Key metrics supporting the decision"""
    
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240122",
        max_tokens=1000,
        system="You are a financial investor",
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
    # Prepare simplified data for the analysis
    last_price = data['Close'].iloc[-1]
    avg_price = data['Close'].mean()
    price_change = (last_price - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
    
    analysis_prompt = f"""Analyze this {ticker} stock data:
    Last price: ${last_price:.2f}
    Average price: ${avg_price:.2f}
    Price change: {price_change:.2f}%
    
    Identify key technical patterns and provide trading insights."""
    
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240122",
        max_tokens=1000,
        system="You are a financial investor",
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
                st.write("Analyzing tickers:", ", ".join(tickers))
                
                # Fetch historical data
                df_dict = {}
                tickers_data = {}
                
                for ticker in tickers:
                    stock = yf.Ticker(ticker)
                    df_dict[ticker] = stock.history(period='2y', interval='1w')
                    tickers_data[ticker] = {
                        'info': {k: str(v) for k, v in stock.info.items()}  # Convert all values to strings
                    }
                
                # Display comparison chart
                st.plotly_chart(create_stock_chart(df_dict))
                
                # Get and display recommendation
                recommendation = get_stock_recommendation(tickers_data)
                st.write("### Investment Recommendation")
                st.write(recommendation)
                
                # Get recommended ticker (assuming it's the first word in the recommendation)
                recommended_ticker = recommendation.split()[0].strip('.,!')
                
                # Create and display candlestick chart
                candlestick_fig, candlestick_data = create_candlestick_chart(recommended_ticker)
                st.plotly_chart(candlestick_fig)
                
                # Get and display technical analysis
                technical_analysis = get_technical_analysis(candlestick_data, recommended_ticker)
                st.write("### Technical Analysis")
                st.write(technical_analysis)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Stack trace:", exc_info=True)

if __name__ == "__main__":
    main()
