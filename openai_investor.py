import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import openai
import pandas as pd
from datetime import datetime

# Set up OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.Client()  # Initialize OpenAI Client

# Helper function to call OpenAI API
def call_openai(prompt, system_message="You are a financial investor. Respond with facts and focused messages as talking to a non-expert."):
    try:
        # Use OpenAI's latest chat completions API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ]
        )
        return response.choices[0].message.content  # Access the content attribute directly
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return ""

# Streamlit app
st.title("Investor Analysis App")

# Input for industry/sub-industry
industry = st.text_input("Enter an industry or sub-industry:", "semiconductors")

if st.button("Get Top Stocks"):
    # Step 1: Retrieve top 5 stock tickers using OpenAI
    prompt = f"Provide the stock tickers of the five companies generally considered most promising for investment in the {industry} industry."
    tickers_response = call_openai(prompt)
    tickers = [t.strip() for t in tickers_response.split(",") if t.strip()]  # Ensure non-empty tickers
    st.write(f"Top 5 stocks in {industry}: {', '.join(tickers)}")

    if len(tickers) > 0:
        # Step 2: Retrieve historical close data
        data = {}
        for ticker in tickers:
            stock_data = yf.Ticker(ticker).history(period="2y", interval="1wk")
            data[ticker] = stock_data["Close"]

        # Combine data into a DataFrame
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

        # Step 3: Retrieve financials, info, and news
        recommendations = []
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            financials = stock.financials
            info = stock.info
            news = stock.news if hasattr(stock, "news") else []

            # Call OpenAI for recommendation
            prompt = f"""
            Analyze the following data for {ticker} and recommend if it is the most interesting stock among these five, with a short explanation.
            Financials: {financials.to_dict()}
            Info: {info}
            News: {news}
            """
            recommendation = call_openai(prompt)
            recommendations.append((ticker, recommendation))

        # Display recommendations and summary financials
        for ticker, recommendation in recommendations:
            st.subheader(f"{ticker}:")
            st.write(recommendation)

            stock = yf.Ticker(ticker)
            info = stock.info
            st.write(f"Market Cap: {info.get('marketCap')}")
            st.write(f"Revenue: {info.get('totalRevenue')}")
            st.write(f"EBITDA: {info.get('ebitda')}")
            st.write(f"P/E Ratio: {info.get('trailingPE')}")
            st.write(f"Yearly Revenue Growth: {info.get('revenueGrowth')}")
            st.write(f"EPS Growth: {info.get('earningsGrowth')}")

            # Step 4: Retrieve and display candlestick chart
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

            # Step 5: Technical analysis (dummy patterns for now)
            st.write("Identified Patterns:")
            for i in range(5):
                st.write(f"Pattern {i+1}: Example pattern on {datetime.now().date()}.")

st.write("Enter an industry and click 'Get Top Stocks' to begin analysis.")
