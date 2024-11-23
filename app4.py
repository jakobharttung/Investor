import streamlit as st
import yfinance as yf
import openai
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Initialize OpenAI API
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.ChatCompletion()

# Function to call GPT-4o for stock ticker recommendations
def get_top_tickers(industry):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial investor, respond with facts and focused messages as talking to a non-expert."},
            {"role": "user", "content": f"List the stock tickers of the top five companies in the {industry} industry based on last year's results and future outlook."}
        ]
    )
    tickers = response['choices'][0]['message']['content'].split()
    return tickers[:5]

# Function to get stock financial data and news
def get_stock_details(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials
    info = stock.info
    news = stock.news
    return financials, info, news

# Function to get stock recommendation
def get_stock_recommendation(tickers_data):
    analysis_prompt = "Analyze the following financial data and analyst sentiment for the listed tickers. Which stock has the best investment potential?"
    tickers_summary = "\n".join([f"{ticker}: {data['info']['shortName']}" for ticker, data in tickers_data.items()])
    prompt = f"{analysis_prompt}\n\n{tickers_summary}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial investor, respond with facts and focused messages as talking to a non-expert."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

# Streamlit App Layout
st.title("Investor Analysis App")
industry = st.text_input("Enter an industry or sub-industry:", value="semiconductors")

# Retrieve Top Stock Tickers
if st.button("Analyze"):
    with st.spinner("Retrieving top tickers..."):
        top_tickers = get_top_tickers(industry)

    # Fetch data for each ticker
    tickers_data = {}
    for ticker in top_tickers:
        stock_data = yf.download(ticker, period="2y", interval="1wk")
        tickers_data[ticker] = {"data": stock_data, "info": yf.Ticker(ticker).info}

    # Plotly line chart for historical data
    fig = go.Figure()
    for ticker, data in tickers_data.items():
        fig.add_trace(go.Scatter(x=data['data'].index, y=data['data']['Close'], name=ticker))
    fig.update_layout(
        title="Stock Prices (Last 2 Years)",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Close Price"),
    )
    st.plotly_chart(fig)

    # Get recommendation from GPT-4o
    with st.spinner("Analyzing stocks for best investment..."):
        recommendation = get_stock_recommendation(tickers_data)
    st.subheader("Recommended Stock for Investment")
    st.write(recommendation)

    # Retrieve detailed financial data for the recommended stock
    best_ticker = recommendation.split(":")[0]
    best_stock = yf.Ticker(best_ticker)
    st.write("**Summary Financials:**")
    st.write({
        "Revenue": best_stock.info.get("totalRevenue"),
        "EBITDA": best_stock.info.get("ebitda"),
        "P/E": best_stock.info.get("trailingPE"),
        "Market Cap": best_stock.info.get("marketCap"),
        "Revenue Growth": best_stock.info.get("revenueGrowth"),
        "EPS Growth": best_stock.info.get("forwardEpsGrowth")
    })

    # Retrieve daily data and visualize candlestick chart
    daily_data = yf.download(best_ticker, period="1y", interval="1d")
    candlestick_fig = go.Figure(data=[go.Candlestick(
        x=daily_data.index,
        open=daily_data['Open'],
        high=daily_data['High'],
        low=daily_data['Low'],
        close=daily_data['Close']
    )])
    candlestick_fig.update_layout(title="Candlestick Chart (Last Year)", xaxis_rangeslider_visible=False)
    st.plotly_chart(candlestick_fig)

    # Add technical analysis patterns (mock example for demo purposes)
    st.write("**Key Technical Patterns Identified:**")
    for idx, date in enumerate(daily_data.index[-5:]):  # Mock: Add last 5 points as patterns
        st.write(f"Pattern {idx+1} on {date}: Bullish breakout")
