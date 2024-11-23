import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import openai
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# Set Streamlit page configuration
st.set_page_config(page_title="Investor Analysis App", layout="wide")

# Initialize OpenAI client using the latest syntax
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.Client()

# Define a function to call OpenAI GPT-4 using the latest syntax
def get_openai_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
        )
        # Access the response content correctly
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return None

# Function to extract tickers from OpenAI response
def extract_tickers(response):
    # Assuming the response is a comma-separated list of tickers
    soup = BeautifulSoup(response, "html.parser")
    text = soup.get_text()
    tickers = [ticker.strip().upper() for ticker in text.replace('\n', ',').split(',') if ticker.strip()]
    # Filter tickers to valid symbols (basic filter)
    tickers = [ticker for ticker in tickers if ticker.isalpha() and len(ticker) <= 5]
    return tickers[:5]

# Function to perform basic technical analysis (placeholder)
def identify_patterns(df):
    patterns = []
    # Simple example: Identify if last day was a bullish engulfing
    if len(df) < 2:
        return patterns
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    if (today['Open'] < today['Close']) and (yesterday['Open'] > yesterday['Close']) and (today['Open'] < yesterday['Close']) and (today['Close'] > yesterday['Open']):
        patterns.append({'pattern': 'Bullish Engulfing', 'date': today.name})
    # Add more patterns as needed
    # This is a placeholder for actual pattern recognition
    # For demonstration, we'll add dummy patterns
    for i in range(0, len(df), max(len(df)//5,1)):
        if i < len(df):
            patterns.append({'pattern': 'Sample Pattern', 'date': df.index[i]})
        if len(patterns) >=5:
            break
    return patterns

# Streamlit App
def main():
    st.title("Investor Analysis App")

    # Industry input
    industry = st.text_input("Enter Industry or Sub-Industry", value="semiconductors")

    if st.button("Analyze"):
        with st.spinner("Fetching and analyzing data..."):
            # Step 1: Get top five tickers from OpenAI
            system_message = {"role": "system", "content": "You are a financial investor, respond with facts and focused messages as talking to a non expert."}
            user_message = {"role": "user", "content": f"List the top five stock tickers in the {industry} industry that are most promising for investment based on their performance over the last year and future outlook."}
            messages = [system_message, user_message]
            response = get_openai_response(messages)
            if response is None:
                st.error("Failed to retrieve tickers.")
                return
            tickers = extract_tickers(response)
            if not tickers:
                st.error("No valid tickers found in the response.")
                return
            st.success(f"Top 5 Tickers: {', '.join(tickers)}")

            # Step 2: Retrieve 2 years of weekly historical close data
            data = yf.download(tickers, period="2y", interval="1wk")['Close']
            if data.empty:
                st.error("Failed to retrieve historical data.")
                return

            # Step 3: Plotly line chart with period selection
            st.subheader("Historical Close Prices")
            # Create buttons for standard periods
            period_buttons = ["1wk", "1mo", "1y", "5y"]
            selected_period = st.radio("Select Period", period_buttons, horizontal=True)

            # Determine the timeframe based on selection
            end_date = datetime.today()
            if selected_period == "1wk":
                start_date = end_date - timedelta(weeks=1)
            elif selected_period == "1mo":
                start_date = end_date - timedelta(days=30)
            elif selected_period == "1y":
                start_date = end_date - timedelta(days=365)
            elif selected_period == "5y":
                start_date = end_date - timedelta(days=365*5)
            else:
                start_date = data.index.min()

            filtered_data = data[data.index >= start_date]

            fig = go.Figure()
            for ticker in tickers:
                fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data[ticker], mode='lines', name=ticker))
            fig.update_layout(height=600, width=1200, hovermode='x unified')

            # Add a range slider
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1wk", step="week", stepmode="backward"),
                            dict(count=1, label="1mo", step="month", stepmode="backward"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(count=5, label="5y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # Step 4: Retrieve financials, info, and news for each ticker
            ticker_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                try:
                    financials = stock.financials
                    info = stock.info
                    news = stock.news
                    ticker_data[ticker] = {
                        'financials': financials,
                        'info': info,
                        'news': news
                    }
                except Exception as e:
                    st.warning(f"Failed to retrieve data for {ticker}: {e}")

            # Step 5: Call OpenAI to recommend the best stock
            recommendation_input = "Based on the following financial data, company info, and recent news, which stock has the best investment potential? Provide your recommendation with justification.\n\n"
            for ticker, data_dict in ticker_data.items():
                recommendation_input += f"Ticker: {ticker}\n"
                # Add summary financials
                try:
                    revenue = data_dict['financials'].loc['Total Revenue'][0]
                    ebitda = data_dict['financials'].loc['EBITDA'][0]
                except:
                    revenue = 'N/A'
                    ebitda = 'N/A'
                try:
                    pe = data_dict['info'].get('trailingPE', 'N/A')
                    market_cap = data_dict['info'].get('marketCap', 'N/A')
                    revenue_growth = data_dict['info'].get('revenueGrowth', 'N/A')
                    eps = data_dict['info'].get('earningsPerShare', 'N/A')
                except:
                    pe = market_cap = revenue_growth = eps = 'N/A'
                recommendation_input += f"Financials:\n- Yearly Revenue: {revenue}\n- EBITDA: {ebitda}\n- P/E: {pe}\n- Market Capitalization: {market_cap}\n- Yearly Growth of Revenue: {revenue_growth}\n- EPS: {eps}\n"
                # Include top 3 news articles' titles
                recent_news = data_dict['news'][:3]
                news_titles = "; ".join([article.get('title', 'N/A') for article in recent_news])
                recommendation_input += f"Recent News Titles: {news_titles}\n\n"

            system_message_recommend = {"role": "system", "content": "You are a financial investor, respond with facts and focused messages as talking to a non expert."}
            user_message_recommend = {"role": "user", "content": recommendation_input}
            messages_recommend = [system_message_recommend, user_message_recommend]
            recommendation_response = get_openai_response(messages_recommend)
            if recommendation_response is None:
                st.error("Failed to get recommendation.")
                return
            # Assume the response is in the format: "Ticker: XYZ\nJustification: ..."
            selected_stock = None
            justification = ""
            for line in recommendation_response.split('\n'):
                if line.startswith("Ticker:"):
                    selected_stock = line.replace("Ticker:", "").strip()
                elif line.startswith("Justification:"):
                    justification = line.replace("Justification:", "").strip()
            if not selected_stock:
                st.error("Failed to parse recommendation.")
                return
            st.success(f"Top Recommended Stock: {selected_stock}")
            st.write(f"**Justification:** {justification}")

            # Display summary financials for the top stock
            top_data = ticker_data.get(selected_stock, {})
            if top_data:
                st.subheader(f"Summary Financials for {selected_stock}")
                try:
                    financials = top_data['financials']
                    info = top_data['info']
                    revenue = financials.loc['Total Revenue'][0]
                    ebitda = financials.loc['EBITDA'][0]
                    pe = info.get('trailingPE', 'N/A')
                    market_cap = info.get('marketCap', 'N/A')
                    revenue_growth = info.get('revenueGrowth', 'N/A')
                    eps = info.get('earningsPerShare', 'N/A')
                    financial_summary = {
                        "Yearly Revenue": revenue,
                        "EBITDA": ebitda,
                        "P/E": pe,
                        "Market Capitalization": market_cap,
                        "Yearly Growth of Revenue": revenue_growth,
                        "EPS": eps
                    }
                    financial_df = pd.DataFrame.from_dict(financial_summary, orient='index', columns=['Value'])
                    st.table(financial_df)
                except Exception as e:
                    st.error(f"Failed to retrieve financial summary: {e}")
            else:
                st.error("No data available for the selected top stock.")

            # Step 6: Retrieve one year of daily data for the top stock
            top_stock = selected_stock
            top_stock_data = yf.download(top_stock, period="1y", interval="1d")
            if top_stock_data.empty:
                st.error("Failed to retrieve daily data for the top stock.")
                return

            # Step 7: Candlestick chart
            st.subheader(f"Daily Candlestick Chart for {top_stock}")
            fig_candlestick = go.Figure(data=[go.Candlestick(
                x=top_stock_data.index,
                open=top_stock_data['Open'],
                high=top_stock_data['High'],
                low=top_stock_data['Low'],
                close=top_stock_data['Close'],
                name='Candlestick'
            )])

            # Step 8: Technical Analysis - Identify patterns
            patterns = identify_patterns(top_stock_data)
            for pattern in patterns:
                fig_candlestick.add_annotation(
                    x=pattern['date'],
                    y=top_stock_data.loc[pattern['date'], 'High'],
                    xref="x",
                    yref="y",
                    text=pattern['pattern'],
                    showarrow=True,
                    arrowhead=1
                )

            fig_candlestick.update_layout(height=600, width=1200, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_candlestick, use_container_width=True)

if __name__ == "__main__":
    main()
