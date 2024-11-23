import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import requests
import openai

# Initialize OpenAI client
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=openai.api_key)

def get_promising_tickers(industry):
    response = client.chat.completions(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial investor, respond with facts and focused messages as talking to a non expert."},
            {"role": "user", "content": f"What are the top five promising companies in the {industry} industry for investment based on last year results and future outlook?"}
        ]
    )
    chat_response = response['choices'][0]['message']['content']
    # Extract tickers from the response, assuming the response is well structured.
    tickers = BeautifulSoup(chat_response, 'html.parser').get_text()
    return tickers.split()[:5]  # Assumes that the tickers are separated by spaces and returns the first five

def fetch_stock_data(tickers):
    data = {}
    for ticker in tickers:
        data[ticker] = yf.Ticker(ticker).history(period="2y", interval="1wk")
    return data

def plot_data(data, ticker):
    fig = go.Figure()
    for t, df in data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=t))
    fig.update_layout(title=f'Weekly Close Prices for {ticker}',
                      xaxis_title='Date',
                      yaxis_title='Close Price',
                      legend_title='Ticker')
    st.plotly_chart(fig, use_container_width=True)

def get_detailed_recommendation(tickers):
    best_ticker = ''
    best_justification = ''
    best_score = -float('inf')
    for ticker in tickers:
        ticker_data = yf.Ticker(ticker)
        financials = ticker_data.financials.to_dict()
        info = ticker_data.info
        news = ticker_data.news  # Simulating news extraction
        recommendation = client.chat.completions(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial investor, respond with quantitative and qualitative analysis."},
                {"role": "user", "content": f"Give a recommendation for {ticker} based on the following data: {financials}, {info}, {news}"}
            ]
        )
        response = recommendation['choices'][0]['message']['content']
        score = float(response.split()[0])  # Example: extract a numeric score from the response
        if score > best_score:
            best_score = score
            best_ticker = ticker
            best_justification = response
    return best_ticker, best_justification

# Streamlit App Interface
st.title("Investor Analysis Tool")

industry = st.text_input("Enter the industry or sub-industry", "semiconductors")
tickers = get_promising_tickers(industry)
st.write("Promising Tickers: ", tickers)

data = fetch_stock_data(tickers)
selected_ticker = st.selectbox("Select Ticker", tickers)
plot_data(data, selected_ticker)

top_stock, justification = get_detailed_recommendation(tickers)
st.write("Top Investment Recommendation: ", top_stock)
st.write("Justification: ", justification)

# Fetch and plot detailed stock data for the top stock
top_stock_data = yf.Ticker(top_stock).history(period="1y")
fig = go.Figure(data=[go.Candlestick(x=top_stock_data.index,
                                     open=top_stock_data['Open'],
                                     high=top_stock_data['High'],
                                     low=top_stock_data['Low'],
                                     close=top_stock_data['Close'])])
fig.update_layout(title=f'Daily Candlestick Chart for {top_stock}',
                  xaxis_title='Date',
                  yaxis_title='Price')
st.plotly_chart(fig, use_container_width=True)
