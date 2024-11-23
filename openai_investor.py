import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import openai
import pandas as pd
import datetime as dt

# OpenAI GPT client setup
openai.api_key = "your_openai_api_key"

# Helper function for OpenAI GPT-4o calls
def call_language_model(prompt, system_message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message["content"]

# Streamlit App
st.title("Investor Analysis App")

# Input for industry or sub-industry
industry = st.text_input("Enter an industry or sub-industry:", "semiconductors")

# Default system persona for the language model
system_message = (
    "You are a financial investor. Respond with facts and focused messages as talking to a non-expert."
)

# Call language model to retrieve stock tickers
if st.button("Retrieve Top Companies"):
    prompt = (
        f"Provide the stock tickers of the top five companies in the {industry} industry, "
        "based on their results over the last year and future outlook."
    )
    tickers_response = call_language_model(prompt, system_message)
    st.write("Language model response:", tickers_response)

    # Extract tickers (assuming comma-separated list in response)
    tickers = [ticker.strip() for ticker in tickers_response.split(",") if ticker]

    # Fetch data using yfinance
    if tickers:
        st.subheader(f"Stock Data for {industry} Industry")
        st.write("Tickers retrieved:", ", ".join(tickers))

        # Retrieve 2 years of weekly data
        end_date = dt.datetime.now()
        start_date = end_date - dt.timedelta(weeks=104)
        data = yf.download(tickers, start=start_date, end=end_date, interval="1wk")

        # Plot the data
        fig = go.Figure()
        for ticker in tickers:
            fig.add_trace(
                go.Scatter(x=data.index, y=data["Close", ticker], mode="lines", name=ticker)
            )
        fig.update_layout(
            title="Weekly Historical Close Prices",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
        )
        st.plotly_chart(fig)

        # Retrieve detailed data and recommendations
        recommendations = []
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            financials = stock.financials
            info = stock.info
            news = stock.news

            # Build prompt for language model
            prompt = (
                f"Given the following data for {ticker}, provide a recommendation on its investment potential:\n"
                f"Financials: {financials.to_dict()}\n"
                f"Info: {info}\n"
                f"Recent News: {news}\n"
                "Please determine which stock has the best investment potential and justify the recommendation."
            )
            recommendation = call_language_model(prompt, system_message)
            recommendations.append((ticker, recommendation))

        # Display the top recommendation
        top_stock, justification = max(recommendations, key=lambda x: x[1])
        st.subheader("Top Stock Recommendation")
        st.write(f"Top stock: {top_stock}")
        st.write(f"Justification: {justification}")

        # Fetch summary financials for top stock
        top_stock_data = yf.Ticker(top_stock)
        info = top_stock_data.info

        st.write("Summary Financials:")
        st.write(
            {
                "Yearly Revenue": info.get("totalRevenue"),
                "EBITDA": info.get("ebitda"),
                "P/E Ratio": info.get("trailingPE"),
                "Market Cap": info.get("marketCap"),
                "Yearly Growth (Revenue)": info.get("revenueGrowth"),
                "EPS Growth": info.get("earningsGrowth"),
            }
        )

        # Retrieve daily data and plot candlestick chart
        st.subheader("Daily Candlestick Chart with Technical Analysis")
        daily_data = top_stock_data.history(period="1y", interval="1d")
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=daily_data.index,
                    open=daily_data["Open"],
                    high=daily_data["High"],
                    low=daily_data["Low"],
                    close=daily_data["Close"],
                )
            ]
        )
        fig.update_layout(title=f"Daily Candlestick Chart for {top_stock}", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig)

        # Add technical analysis notes
        st.write("Identified Patterns:")
        # Example patterns (replace with actual analysis logic)
        patterns = [
            {"date": "2023-02-15", "pattern": "Bullish Engulfing"},
            {"date": "2023-04-10", "pattern": "Double Bottom"},
        ]
        for pattern in patterns:
            st.write(f"Date: {pattern['date']}, Pattern: {pattern['pattern']}")
