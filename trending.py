import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import anthropic
from anthropic import Anthropic
import pytz
import ta

# Streamlit app setup
st.set_page_config(page_title="Investor Analysis App", layout="wide")
st.title("Investor Analysis App")

# Anthropic API setup
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = Anthropic(api_key=anthropic_api_key)

# Function to get stock data
def get_stock_data(ticker, period="1y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

# Function to identify crossover events
def identify_crossovers(data):
    data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['SMA50'] = ta.trend.sma_indicator(data['Close'], window=50)
    
    crossovers = []
    for i in range(1, len(data)):
        if (data['SMA20'].iloc[i-1] <= data['SMA50'].iloc[i-1] and 
            data['SMA20'].iloc[i] > data['SMA50'].iloc[i]):
            crossovers.append((data.index[i], 'up'))
        elif (data['SMA20'].iloc[i-1] >= data['SMA50'].iloc[i-1] and 
              data['SMA20'].iloc[i] < data['SMA50'].iloc[i]):
            crossovers.append((data.index[i], 'down'))
    
    return crossovers

# Function to get news for a company
def get_company_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    name = stock.info['longname']
    news = yf.Ticker(name).news
    utc = pytz.UTC
    start_date = utc.localize(start_date)
    end_date = utc.localize(end_date)
    filtered_news = [n for n in news if start_date <= datetime.fromtimestamp(n['providerPublishTime'], tz=utc) <= end_date]
    return filtered_news

# Function to get company info
def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    return {
        'info': info,
        'financials': financials.to_dict(),
        'balance_sheet': balance_sheet.to_dict()
    }

# Function to analyze crossover events
def analyze_crossover(event_date, event_type, news, company_info):
    news_summary = "\n".join([f"- {n['title']}" for n in news[:5]])  # Summarize up to 5 news items
    
    prompt = f"""
    As a financial investor, analyze the following crossover event and provide insights:

    Event Date: {event_date.strftime('%Y-%m-%d')}
    Event Type: {event_type}

    Recent News:
    {news_summary}

    Company Information:
    - Name: {company_info['info'].get('longName', 'N/A')}
    - Sector: {company_info['info'].get('sector', 'N/A')}
    - Industry: {company_info['info'].get('industry', 'N/A')}
    - Market Cap: ${company_info['info'].get('marketCap', 'N/A'):,}

    Please provide a focused analysis of notable events, facts, company communications such as product announcements, investor events, M&A news, or strategy changes that could explain this crossover. Avoid technical jargon about bullish or bearish moments, and instead focus on concrete business factors. Provide both quantitative and qualitative insights in your response.
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are a financial investor, respond with facts and focused messages as talking to a non expert.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

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
            font=dict(size=20, color='blue' if event_type == 'up' else 'black')
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

st.sidebar.write("This app analyzes stock data and provides insights on trend changes.")
