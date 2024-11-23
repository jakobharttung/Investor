import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import openai
from bs4 import BeautifulSoup
import requests
import pandas as pd

# Set the OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up the Streamlit app title
st.title("Investor Analysis App")

# Input for industry or sub-industry with 'semiconductors' as default
industry = st.text_input("Enter an industry or sub-industry:", value="semiconductors")

if industry:
    # System prompt for the language model
    system_prompt = "You are a financial investor, respond with facts and focused messages as talking to a non expert."

    # User prompt to retrieve the top five stock tickers
    user_prompt = f"Please provide the stock tickers of the top five {industry} companies generally considered most promising for investment based on their results over the last year and future outlook. Only provide the stock tickers, separated by commas."

    # Call the OpenAI API to get the tickers
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # Replace with the correct model name if different
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract the response and tickers
    tickers_text = response['choices'][0]['message']['content']
    tickers = [ticker.strip().upper() for ticker in tickers_text.split(',')]

    st.write(f"**Top five companies in {industry} industry:** {', '.join(tickers)}")

    # Retrieve 2 years of weekly historical close data for all tickers
    data = yf.download(tickers, period='2y', interval='1wk')['Close']

    # Plot the data using Plotly
    fig = go.Figure()
    for ticker in tickers:
        fig.add_trace(go.Scatter(x=data.index, y=data[ticker], mode='lines', name=ticker))

    # Add range selector and buttons
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label='1wk', step='week', stepmode='backward'),
                    dict(count=1, label='1mo', step='month', stepmode='backward'),
                    dict(count=1, label='1y', step='year', stepmode='backward'),
                    dict(count=5, label='5y', step='year', stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(visible=True),
            type='date'
        )
    )

    st.plotly_chart(fig)

    # Retrieve financials, info, and news for each ticker
    recommendations = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        info = stock.info
        news = stock.news

        # Prepare data for the language model
        financial_data_str = f"Financials: {financials.to_string()}, Info: {info}, News Headlines: {[n['title'] for n in news]}"

        # User prompt to get recommendation
        user_prompt = f"Based on the following data, assess the investment potential of {ticker}:\n{financial_data_str}\nProvide a recommendation focusing on analyst sentiment and financial data."

        # Call the OpenAI API to get the recommendation
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        recommendation = response['choices'][0]['message']['content']
        recommendations.append({'ticker': ticker, 'recommendation': recommendation})

    # Determine the top stock based on the recommendations
    top_recommendation = max(recommendations, key=lambda x: x['recommendation'].count('buy'))
    top_stock = top_recommendation['ticker']
    justification = top_recommendation['recommendation']

    st.write(f"### Top Recommended Stock: **{top_stock}**")
    st.write(justification)

    # Retrieve summary financials for the top stock
    stock = yf.Ticker(top_stock)
    info = stock.info

    # Extract required financials
    summary_financials = {
        'Yearly Revenue': info.get('totalRevenue'),
        'EBITDA': info.get('ebitda'),
        'P/E Ratio': info.get('trailingPE'),
        'Market Capitalization': info.get('marketCap'),
        'Yearly Revenue Growth': info.get('revenueGrowth'),
        'EPS Growth': info.get('earningsGrowth')
    }

    st.write("### Summary Financials:")
    for key, value in summary_financials.items():
        st.write(f"**{key}:** {value}")

    # Retrieve one year of daily data for the top stock
    data = yf.download(top_stock, period='1y', interval='1d')

    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])

    # Perform technical analysis to identify key five patterns
    # For demonstration, identify highest high, lowest low, golden cross, death cross, RSI signals

    # Highest high
    highest_high = data['High'].max()
    highest_high_date = data['High'].idxmax()

    # Lowest low
    lowest_low = data['Low'].min()
    lowest_low_date = data['Low'].idxmin()

    # Simple Moving Averages for golden/death cross
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()

    # Golden Cross
    golden_cross = data[(data['SMA50'] > data['SMA200']) & (data['SMA50'].shift(1) <= data['SMA200'].shift(1))]
    golden_cross_date = golden_cross.index[0] if not golden_cross.empty else None

    # Death Cross
    death_cross = data[(data['SMA50'] < data['SMA200']) & (data['SMA50'].shift(1) >= data['SMA200'].shift(1))]
    death_cross_date = death_cross.index[0] if not death_cross.empty else None

    # RSI calculation
    delta = data['Close'].diff()
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    RS = roll_up / roll_down
    data['RSI'] = 100.0 - (100.0 / (1.0 + RS))

    # Overbought and Oversold
    overbought = data[data['RSI'] > 70]
    overbought_date = overbought.index[0] if not overbought.empty else None

    oversold = data[data['RSI'] < 30]
    oversold_date = oversold.index[0] if not oversold.empty else None

    # Add annotations to the chart
    annotations = []

    if highest_high_date:
        annotations.append(dict(
            x=highest_high_date,
            y=highest_high,
            xref='x',
            yref='y',
            text='Highest High',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        ))

    if lowest_low_date:
        annotations.append(dict(
            x=lowest_low_date,
            y=lowest_low,
            xref='x',
            yref='y',
            text='Lowest Low',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=40
        ))

    if golden_cross_date:
        annotations.append(dict(
            x=golden_cross_date,
            y=data.loc[golden_cross_date, 'Close'],
            xref='x',
            yref='y',
            text='Golden Cross',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        ))

    if death_cross_date:
        annotations.append(dict(
            x=death_cross_date,
            y=data.loc[death_cross_date, 'Close'],
            xref='x',
            yref='y',
            text='Death Cross',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=40
        ))

    if overbought_date:
        annotations.append(dict(
            x=overbought_date,
            y=data.loc[overbought_date, 'High'],
            xref='x',
            yref='y',
            text='RSI Overbought',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        ))

    if oversold_date:
        annotations.append(dict(
            x=oversold_date,
            y=data.loc[oversold_date, 'Low'],
            xref='x',
            yref='y',
            text='RSI Oversold',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=40
        ))

    fig.update_layout(annotations=annotations)

    st.plotly_chart(fig)
