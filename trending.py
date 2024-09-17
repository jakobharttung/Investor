import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import anthropic
from anthropic import Anthropic
import pytz
import ta

# ... (previous code remains the same)

# Function to get news for a company
def get_company_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    news = stock.news
    utc = pytz.UTC
    start_date = utc.localize(start_date)
    end_date = utc.localize(end_date)
    filtered_news = [n for n in news if start_date <= datetime.fromtimestamp(n['providerPublishTime'], tz=utc) <= end_date]
    return filtered_news

# ... (rest of the previous code remains the same)

# Main app
ticker = st.text_input("Enter a stock ticker:", value="AAPL")

if ticker:
    # Get stock data
    data = get_stock_data(ticker)
    
    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'])])
    
    # Identify crossover events
    crossovers = identify_crossovers(data)
    
    # Add crossover events to the chart
    for date, event_type in crossovers:
        fig.add_annotation(
            x=date,
            y=data.loc[date, 'High'] if event_type == 'up' else data.loc[date, 'Low'],
            text='↑' if event_type == 'up' else '↓',
            showarrow=False,
            font=dict(size=20, color='green' if event_type == 'up' else 'red')
        )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Get company info
    company_info = get_company_info(ticker)
    
    # Analyze crossover events
    st.subheader("Crossover Event Analysis")
    for date, event_type in crossovers:
        start_date = date.replace(tzinfo=None) - timedelta(days=60)
        end_date = date.replace(tzinfo=None)
        news = get_company_news(ticker, start_date, end_date)
        
        analysis = analyze_crossover(date, event_type, news, company_info)
        
        st.write(f"**Event Date:** {date.strftime('%Y-%m-%d')}")
        st.write(f"**Event Type:** {'Upward' if event_type == 'up' else 'Downward'} Trend")
        st.write(f"**Analysis:**")
        st.write(analysis)
        st.write("---")

# ... (rest of the code remains the same)
