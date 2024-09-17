import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from anthropic import Anthropic
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# Initialize Anthropic client
anthropic = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def get_llm_response(prompt):
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are a financial investor, respond with facts and clear messages.",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

st.title("Investor Analyst App")

company = st.text_input("Enter a company name:")

if company:
    # Get tickers
    tickers_prompt = f"Provide the stock ticker for {company} and 5 other tickers for competitors in the same industry of comparable size and strategy. Format the response as a comma-separated list of tickers only."
    tickers_response = get_llm_response(tickers_prompt)
    tickers = [ticker.strip() for ticker in tickers_response.split(',')]

    # Fetch historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    data = yf.download(tickers, start=start_date, end=end_date)

    # Create interactive chart
    fig = go.Figure()
    for ticker in tickers:
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'][ticker], mode='lines', name=ticker))

    fig.update_layout(
        title="Stock Price History",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode="x unified"
    )

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
        stock = yf.Ticker(ticker)
        financials = stock.financials
        info = stock.info
        news = stock.news
        str.write('news')
        # Sentiment analysis
        sentiment_prompt = f"Perform a sentiment analysis on the following financial data, company info, and news for {ticker}: {financials}, {info}, {news}. Provide a short summary of the sentiment."
        sentiment = get_llm_response(sentiment_prompt)

        # Analyst consensus
        consensus_prompt = f"Based on the available data, what is the analyst consensus for {ticker}? Provide a short summary."
        consensus = get_llm_response(consensus_prompt)

        # Overall analysis
        analysis_prompt = f"Provide an overall analysis of {ticker} within its industry based on the following information: {financials}, {info}, {news}, {sentiment}, {consensus}. Keep the analysis concise."
        analysis = get_llm_response(analysis_prompt)

        analyses[ticker] = {
            "sentiment": sentiment,
            "consensus": consensus,
            "analysis": analysis
        }

    # Generate recommendation
    recommendation_prompt = f"Based on the following analyses of {company} and its competitors {analyses}, provide an investment recommendation for {company}: Buy, Hold, or Sell. Include a short explanation for the recommendation."
    recommendation = get_llm_response(recommendation_prompt)

    # Generate key financial metrics
    metrics_prompt = f"Based on the recommendation '{recommendation}' and the analyses {analyses}, what are the key financial metrics supporting this recommendation for {company}? Provide a concise list of the most important metrics and their values."
    key_metrics = get_llm_response(metrics_prompt)

    # Display results
    st.subheader("Investment Recommendation")
    st.write(recommendation)

    st.subheader("Key Financial Metrics")
    st.write(key_metrics)
