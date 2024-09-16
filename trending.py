import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import os
from anthropic import Anthropic
from datetime import datetime, timedelta
import ta

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    # Get data for the last 2 years instead of year-to-date
    data = stock.history(period="2y")
    return data

def calculate_moving_averages(data):
    # Use 20-day SMA instead of 50-day for more frequent crossovers
    data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['SMA50'] = ta.trend.sma_indicator(data['Close'], window=50)
    return data

def identify_crossovers(data):
    crossovers = []
    for i in range(1, len(data)):
        # Check if SMA20 crosses above SMA50
        if (data['SMA20'].iloc[i-1] <= data['SMA50'].iloc[i-1] and 
            data['SMA20'].iloc[i] > data['SMA50'].iloc[i]):
            crossovers.append(('golden', data.index[i]))
        # Check if SMA20 crosses below SMA50
        elif (data['SMA20'].iloc[i-1] >= data['SMA50'].iloc[i-1] and 
              data['SMA20'].iloc[i] < data['SMA50'].iloc[i]):
            crossovers.append(('death', data.index[i]))
    return crossovers

def create_candlestick_chart(data, crossovers, explanations):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'])])

    # Add SMA lines to the chart
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA20', line=dict(color='blue', width=1)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA50', line=dict(color='red', width=1)))

    for i, (cross_type, date) in enumerate(crossovers):
        color = 'green' if cross_type == 'golden' else 'red'
        symbol = 'triangle-up' if cross_type == 'golden' else 'triangle-down'
        fig.add_trace(go.Scatter(
            x=[date],
            y=[data.loc[date, 'High'] if cross_type == 'golden' else data.loc[date, 'Low']],
            mode='markers+text',
            marker=dict(symbol=symbol, size=15, color=color),
            text=[explanations[i]],
            textposition='top center' if cross_type == 'golden' else 'bottom center',
            showlegend=False
        ))

    fig.update_layout(title=f'{ticker} Stock Price', xaxis_title='Date', yaxis_title='Price')
    return fig

st.title('Stock Trend Analysis')

ticker = st.text_input('Enter Stock Ticker:', value='AAPL')

if ticker:
    data = get_stock_data(ticker)
    data = calculate_moving_averages(data)
    crossovers = identify_crossovers(data)

    if not crossovers:
        st.warning("No crossovers detected in the given time period.")
    else:
        explanations = []
        for cross_type, date in crossovers:
            news = get_news(ticker, date)
            explanation = analyze_reversal(ticker, cross_type, date, news)
            explanations.append(explanation)

        fig = create_candlestick_chart(data, crossovers, explanations)
        st.plotly_chart(fig)

        st.subheader('Trend Reversals')
        for i, (cross_type, date) in enumerate(crossovers):
            st.write(f"{cross_type.capitalize()} Cross on {date.date()}: {explanations[i]}")
