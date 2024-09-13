import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
import datetime as dt
import openai  # Assuming this is used to connect to Anthropic Claude

# Load the API key from Streamlit secrets
openai.api_key = st.secrets["anthropic"]["api_key"]

# Function to call Anthropic Claude for explanations
def get_explanations(news_list):
    explanations = []
    for news in news_list:
        # Call to Claude for generating explanation (pseudo-code, replace with real call)
        response = openai.Completion.create(
            model="claude-model",  # Use the correct model endpoint
            prompt=f"Explain the market impact of this news: {news}",
            max_tokens=100
        )
        explanations.append(response.choices[0].text)
    return explanations

# Function to fetch news related to stock around key dates
def get_news_around_dates(ticker, dates):
    news = []
    for date in dates:
        # Fetch news using yfinance or a news API for the given date (pseudo-code)
        news.append(f"News on {date} for {ticker}")  # Replace with actual news retrieval function
    return news

# App Title
st.title("Stock Technical Analysis with Reversal Explanations")

# Step 1: Ticker Entry
ticker = st.text_input('Enter Stock Ticker', 'AAPL')

# Retrieve stock data for the current year
if ticker:
    stock_data = yf.download(ticker, start="2023-01-01", end=dt.datetime.today().strftime('%Y-%m-%d'))

    # Step 2: Plot Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                         open=stock_data['Open'],
                                         high=stock_data['High'],
                                         low=stock_data['Low'],
                                         close=stock_data['Close'])])

    # Step 3: Calculate moving averages and detect crosses
    stock_data['SMA50'] = ta.sma(stock_data['Close'], length=50)  # 50-day SMA
    stock_data['SMA200'] = ta.sma(stock_data['Close'], length=200)  # 200-day SMA

    # Detect Golden and Dead Crosses
    stock_data['Golden Cross'] = (stock_data['SMA50'] > stock_data['SMA200']) & (stock_data['SMA50'].shift(1) <= stock_data['SMA200'].shift(1))
    stock_data['Dead Cross'] = (stock_data['SMA50'] < stock_data['SMA200']) & (stock_data['SMA50'].shift(1) >= stock_data['SMA200'].shift(1))

    # Plot arrows for golden and dead crosses
    for i in range(len(stock_data)):
        if stock_data['Golden Cross'].iloc[i]:
            fig.add_annotation(x=stock_data.index[i], y=stock_data['High'].iloc[i],
                               text="🡅", showarrow=True, arrowhead=1, arrowsize=2, font=dict(color="green"))
        if stock_data['Dead Cross'].iloc[i]:
            fig.add_annotation(x=stock_data.index[i], y=stock_data['Low'].iloc[i],
                               text="🡇", showarrow=True, arrowhead=1, arrowsize=2, font=dict(color="red"))

    # Display the chart
    fig.update_layout(title=f"Daily Candlestick Chart for {ticker}",
                      xaxis_title="Date",
                      yaxis_title="Price",
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)

    # Step 4: Fetch news around golden and dead cross dates
    golden_dates = stock_data[stock_data['Golden Cross']].index
    dead_dates = stock_data[stock_data['Dead Cross']].index

    golden_news = get_news_around_dates(ticker, golden_dates)
    dead_news = get_news_around_dates(ticker, dead_dates)

    # Step 5: Generate explanations for reversals
    golden_explanations = get_explanations(golden_news)
    dead_explanations = get_explanations(dead_news)

    # Step 6: Annotate the chart with explanations
    for i, date in enumerate(golden_dates):
        fig.add_annotation(x=date, y=stock_data.loc[date]['High'],
                           text=f"🡅 {golden_explanations[i]}",
                           showarrow=True, arrowhead=1, arrowsize=1, font=dict(color="green"))

    for i, date in enumerate(dead_dates):
        fig.add_annotation(x=date, y=stock_data.loc[date]['Low'],
                           text=f"🡇 {dead_explanations[i]}",
                           showarrow=True, arrowhead=1, arrowsize=1, font=dict(color="red"))

    # Display the updated chart with explanations
    st.plotly_chart(fig)
