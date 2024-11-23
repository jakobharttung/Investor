import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import anthropic
from bs4 import BeautifulSoup
import json

# Initialize Anthropic client
client = anthropic.Client(api_key=st.secrets["ANTHROPIC_API_KEY"])

def get_tickers_from_industry(industry):
    prompt = f"""As a financial investment expert, please provide the stock tickers of the five most promising companies for investment in the {industry} industry. 
    Consider market position, growth potential, and financial stability. 
    Return only the tickers in a comma-separated format."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": prompt}]
    )
    
    tickers = message.content[0].text.strip().split(',')
    return [t.strip() for t in tickers]

def create_stock_chart(tickers, period='2y', interval='1wk'):
    fig = go.Figure()
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'],
                                mode='lines', name=ticker))
    
    fig.update_layout(
        title='Stock Price History',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    return fig

def analyze_stocks(tickers):
    analysis_prompt = f"""As a financial analyst, please analyze these companies {', '.join(tickers)} and recommend the most promising investment.
    Consider recent financial performance, market position, and growth prospects.
    Provide a clear recommendation with brief justification."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    
    return message.content[0].text

def technical_analysis(ticker_data):
    prompt = f"""As a technical analyst, please identify five key technical patterns in this stock's price movement over the past year.
    Consider support/resistance levels, trend lines, and classic patterns.
    Format each pattern as: Pattern Name: Brief explanation"""
    
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text

def main():
    st.title('Industry Stock Analysis')
    
    industry = st.text_input('Enter Industry', value='semiconductors')
    
    if industry:
        tickers = get_tickers_from_industry(industry)
        
        # Historical price chart
        periods = ['1m', '3m', '6m', '1y', '2y', '5y']
        selected_period = st.select_slider('Select Period', options=periods, value='2y')
        
        chart = create_stock_chart(tickers, period=selected_period)
        st.plotly_chart(chart)
        
        # Stock analysis
        analysis = analyze_stocks(tickers)
        st.subheader('Investment Recommendation')
        st.write(analysis)
        
        # Get recommended ticker (assuming it's the first mentioned in the analysis)
        recommended_ticker = tickers[0]  # This should be extracted from analysis
        
        # Display financials
        stock = yf.Ticker(recommended_ticker)
        st.subheader(f'{recommended_ticker} Financial Summary')
        financials = stock.financials
        st.dataframe(financials.head())
        
        # Candlestick chart
        hist = stock.history(period='1y', interval='1d')
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                            open=hist['Open'],
                                            high=hist['High'],
                                            low=hist['Low'],
                                            close=hist['Close'])])
        
        # Technical analysis
        patterns = technical_analysis(hist)
        st.subheader('Technical Analysis')
        st.write(patterns)
        
        fig.update_layout(title=f'{recommended_ticker} Price Chart',
                         xaxis_title='Date',
                         yaxis_title='Price')
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
