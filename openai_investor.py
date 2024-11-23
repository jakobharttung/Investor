import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import openai
import pandas as pd
from datetime import datetime

# Set up OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Helper function to call OpenAI GPT-4o
def call_gpt4o(prompt, system_message="You are a financial investor. Respond with facts and focused messages as talking to a non-expert."):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]

# Streamlit app
st.title("Investor Analysis App")

# Input for industry/sub-industry
industry = st.text_input("Enter an industry or sub-industry:", "semiconductors")

# Step 1: Retrieve top 5 stock tickers using GPT-4o
if st.button("Get Top Stocks"):
    prompt = f"Provide the stock tickers of the five companies generally considered most promising for investment in the {industry} industry."
    tickers_response = call_gpt4o(prompt)
    tickers = [t.strip() for t in tickers_response.split(",")][:5]
    st.write(f"Top 5 stocks in {industry}: {', '.join(tickers)}")

    # Retrieve historical close data
    data = {}
    for ticker in tickers:
        data[ticker] = yf.Ticker(ticker).history(period="2y", interval="1wk")["Close"]

    # Combine data into one DataFrame
    df = pd.DataFrame(data)

    # Plotly line chart
    fig = go.Figure()
    for ticker in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[ticker], mode="lines", name=ticker))
    fig.update_layout(
        title="Weekly Historical Close Prices",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,
        xaxis=dict(rangeselector=dict(
            buttons=list([
                dict(count=1, label="1wk", step="week", stepmode="backward"),
                dict(count=1, label="1mo", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )),
    )
    st.plotly_chart(fig)

    # Retrieve financials, info, and news
    recommendations = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        info = stock.info
        news = stock.news

        # Call GPT-4o for recommendation
        prompt = f"""
        Given the financials, company info, and recent news, recommend whether {ticker} is the most interesting stock among the five, with a short explanation.
        Financials: {financials.to_dict()}
        Info: {info}
        News: {news}
        """
        recommendation = call_gpt4o(prompt)
        recommendations.append((ticker, recommendation))

    # Display recommendations
    for ticker, recommendation in recommendations:
        st.subheader(f"{ticker}:")
        st.write(recommendation)

        # Display summary financials
        stock = yf.Ticker(ticker)
        info = stock.info
        st.write(f"Market Cap: {info.get('marketCap')}")
        st.write(f"Revenue: {info.get('totalRevenue')}")
        st.write(f"EBITDA: {info.get('ebitda')}")
        st.write(f"P/E Ratio: {info.get('trailingPE')}")
        st.write(f"Yearly Revenue Growth: {info.get('revenueGrowth')}")
        st.write(f"EPS Growth: {info.get('earningsGrowth')}")

        # Retrieve and display candlestick chart
        df_candlestick = stock.history(period="1y", interval="1d")[["Open", "High", "Low", "Close"]]
        fig_candlestick = go.Figure(data=[go.Candlestick(
            x=df_candlestick.index,
            open=df_candlestick["Open"],
            high=df_candlestick["High"],
            low=df_candlestick["Low"],
            close=df_candlestick["Close"]
        )])
        fig_candlestick.update_layout(title=f"Candlestick Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig_candlestick)

        # Technical analysis pattern identification (dummy example)
        st.write("Identified Patterns:")
        for i in range(5):
            st.write(f"Pattern {i+1}: Example pattern description on {datetime.now().date()}.")

st.write("Enter an industry and click 'Get Top Stocks' to begin analysis.")
