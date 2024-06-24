import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from anthropic import Anthropic
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
client = Anthropic(api_key=anthropic_api_key)

def get_stock_data(ticker, period="5y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def get_company_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

def get_company_news(ticker):
    stock = yf.Ticker(ticker)
    return stock.news

def get_company_financials(ticker):
    stock = yf.Ticker(ticker)
    return stock.financials

def call_anthropic(prompt):
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system="You are a financial investor, respond with facts and clear messages",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def main():
    st.title("Investor Analyst App")

    company = st.text_input("Enter a company name:")

    if company:
        # Get stock ticker and competitors
        prompt = f"As a financial investor, provide the stock ticker for {company} and 3 other tickers for its main competitors in the same industry. Format the response as a Python list of strings, with the first element being the ticker for {company}."
        tickers_response = call_anthropic(prompt)
        tickers = tickers_response
        st.write(tickers)
        for ticker in tickers:
            st.write(ticker)
        # Get historical data for all tickers
        data = {ticker: get_stock_data(ticker) for ticker in tickers}
        st.write(data)
        # Create plotly chart
        fig = go.Figure()
        for ticker, stock_data in data.items():
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name=ticker))

        fig.update_layout(title="Stock Price Comparison", xaxis_title="Date", yaxis_title="Price")
        
        # Add range slider and buttons
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )

        st.plotly_chart(fig)

        # Analyze each ticker
        analyses = {}
        for ticker in tickers:
            st.write(ticker)
            info = get_company_info(ticker)
            news = get_company_news(ticker)
            financials = get_company_financials(ticker)

            prompt = f"As a financial investor, perform a sentiment analysis on this data for {ticker}: {info}\n{news}\n{financials}"
            sentiment = call_anthropic(prompt)

            prompt = f"As a financial investor, provide an analyst consensus on {ticker} based on this data: {info}\n{news}\n{financials}"
            consensus = call_anthropic(prompt)

            prompt = f"As a financial investor, provide an overall analysis of {ticker} within its industry based on this data: {info}\n{news}\n{financials}"
            industry_analysis = call_anthropic(prompt)

            analyses[ticker] = {
                "sentiment": sentiment,
                "consensus": consensus,
                "industry_analysis": industry_analysis
            }

        # Generate recommendation
        prompt = f"As a financial investor, based on these analyses, generate a recommendation (Buy, Hold, or Sell) for investing in {company} with a short explanation: {analyses}"
        recommendation = call_anthropic(prompt)

        # Generate key financial metrics
        prompt = f"As a financial investor, provide the key financial metrics supporting the recommendation for {company} based on this data: {analyses}"
        metrics = call_anthropic(prompt)

        # Display results
        st.subheader("Investment Recommendation")
        st.write(recommendation)

        st.subheader("Key Financial Metrics")
        st.write(metrics)

if __name__ == "__main__":
    main()
