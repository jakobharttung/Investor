import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import openai
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import ta

# Set Streamlit page configuration
st.set_page_config(page_title="Investor Analysis App", layout="wide")

# Initialize OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define a function to call OpenAI GPT-4 using the latest syntax
def get_openai_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
        )
        # Access the response content correctly using dictionary-style access
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return None

# Function to extract tickers from OpenAI response
def extract_tickers(response):
    # Assuming the response is a comma-separated list of tickers or listed in lines
    soup = BeautifulSoup(response, "html.parser")
    text = soup.get_text()
    # Split by comma and newline
    tickers = [ticker.strip().upper() for ticker in text.replace('\n', ',').split(',') if ticker.strip()]
    # Filter tickers to valid symbols (basic filter: alphabetic and up to 5 characters)
    tickers = [ticker for ticker in tickers if ticker.isalpha() and len(ticker) <= 5]
    return tickers[:5]

# Function to perform sophisticated technical analysis using the ta library
def identify_patterns(df):
    patterns = []
    # Ensure the dataframe has the necessary columns
    if not {'Open', 'High', 'Low', 'Close'}.issubset(df.columns):
        return patterns
    
    # Calculate Moving Averages
    sma50 = ta.trend.SMAIndicator(close=df['Close'], window=50)
    df['SMA50'] = sma50.sma_indicator()
    sma200 = ta.trend.SMAIndicator(close=df['Close'], window=200)
    df['SMA200'] = sma200.sma_indicator()
    
    # Calculate MACD
    macd = ta.trend.MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()
    
    # Calculate RSI
    rsi = ta.momentum.RSIIndicator(close=df['Close'])
    df['RSI'] = rsi.rsi()
    
    # Identify Golden Cross and Death Cross
    if df['SMA50'].iloc[-1] > df['SMA200'].iloc[-1] and df['SMA50'].iloc[-2] <= df['SMA200'].iloc[-2]:
        patterns.append({'pattern': 'Golden Cross', 'date': df.index[-1]})
    elif df['SMA50'].iloc[-1] < df['SMA200'].iloc[-1] and df['SMA50'].iloc[-2] >= df['SMA200'].iloc[-2]:
        patterns.append({'pattern': 'Death Cross', 'date': df.index[-1]})
    
    # Identify MACD Crossovers
    if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD_Signal'].iloc[-2]:
        patterns.append({'pattern': 'MACD Bullish Crossover', 'date': df.index[-1]})
    elif df['MACD'].iloc[-1] < df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD_Signal'].iloc[-2]:
        patterns.append({'pattern': 'MACD Bearish Crossover', 'date': df.index[-1]})
    
    # Identify RSI Overbought/Oversold
    if df['RSI'].iloc[-1] > 70:
        patterns.append({'pattern': 'RSI Overbought', 'date': df.index[-1]})
    elif df['RSI'].iloc[-1] < 30:
        patterns.append({'pattern': 'RSI Oversold', 'date': df.index[-1]})
    
    # Limit to 5 patterns
    return patterns[:5]

# Streamlit App
def main():
    st.title("Investor Analysis App")
    
    st.write("""
    ### Analyze Top Stocks in an Industry
    Enter an industry or sub-industry to analyze the top 5 promising stocks based on past performance and future outlook.
    """)
    
    # Industry input
    industry = st.text_input("Enter Industry or Sub-Industry", value="semiconductors")
    
    if st.button("Analyze"):
        with st.spinner("Fetching and analyzing data..."):
            # Step 1: Get top five tickers from OpenAI
            system_message = {
                "role": "system",
                "content": "You are a financial investor, respond with facts and focused messages as talking to a non expert."
            }
            user_message = {
                "role": "user",
                "content": f"List the top five stock tickers in the {industry} industry that are most promising for investment based on their performance over the last year and future outlook."
            }
            messages = [system_message, user_message]
            response = get_openai_response(messages)
            if response is None:
                st.error("Failed to retrieve tickers.")
                return
            tickers = extract_tickers(response)
            if not tickers:
                st.error("No valid tickers found in the response.")
                return
            st.success(f"**Top 5 Tickers:** {', '.join(tickers)}")
            
            # Step 2: Retrieve 2 years of weekly historical close data
            @st.cache_data
            def fetch_historical_close(tickers):
                data = yf.download(tickers, period="2y", interval="1wk")['Close']
                return data

            data = fetch_historical_close(tickers)
            if data.empty:
                st.error("Failed to retrieve historical data.")
                return
            
            # Step 3: Plotly line chart with period selection
            st.subheader("Historical Close Prices")
            # Create radio buttons for standard periods
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
                recommendation_input += f"**Ticker:** {ticker}\n"
                # Add summary financials
                try:
                    revenue = data_dict['financials'].loc['Total Revenue'][0]
                except:
                    revenue = 'N/A'
                try:
                    ebitda = data_dict['financials'].loc['EBITDA'][0]
                except:
                    ebitda = 'N/A'
                try:
                    pe = data_dict['info'].get('trailingPE', 'N/A')
                except:
                    pe = 'N/A'
                try:
                    market_cap = data_dict['info'].get('marketCap', 'N/A')
                except:
                    market_cap = 'N/A'
                try:
                    revenue_growth = data_dict['info'].get('revenueGrowth', 'N/A')
                except:
                    revenue_growth = 'N/A'
                try:
                    eps = data_dict['info'].get('earningsPerShare', 'N/A')
                except:
                    eps = 'N/A'
                
                recommendation_input += f"**Financials:**\n- Yearly Revenue: {revenue}\n- EBITDA: {ebitda}\n- P/E Ratio: {pe}\n- Market Capitalization: {market_cap}\n- Yearly Growth of Revenue: {revenue_growth}\n- EPS: {eps}\n"
                
                # Include top 3 news articles' titles
                recent_news = data_dict['news'][:3]
                news_titles = "; ".join([article.get('title', 'N/A') for article in recent_news])
                recommendation_input += f"**Recent News Titles:** {news_titles}\n\n"
            
            system_message_recommend = {
                "role": "system",
                "content": "You are a financial investor, respond with facts and focused messages as talking to a non expert."
            }
            user_message_recommend = {
                "role": "user",
                "content": recommendation_input
            }
            messages_recommend = [system_message_recommend, user_message_recommend]
            recommendation_response = get_openai_response(messages_recommend)
            if recommendation_response is None:
                st.error("Failed to get recommendation.")
                return
            
            # Parse the response to extract selected stock and justification
            selected_stock = None
            justification = ""
            lines = recommendation_response.split('\n')
            for line in lines:
                if line.lower().startswith("ticker:"):
                    selected_stock = line.split(":", 1)[1].strip()
                elif line.lower().startswith("justification:"):
                    justification = line.split(":", 1)[1].strip()
            
            if not selected_stock:
                # Attempt to extract ticker from response using heuristics
                words = recommendation_response.split()
                for word in words:
                    if word.isupper() and len(word) <= 5:
                        selected_stock = word
                        break
                if not selected_stock:
                    st.error("Failed to parse recommendation.")
                    return
            
            st.success(f"**Top Recommended Stock:** {selected_stock}")
            st.write(f"**Justification:** {justification}")
            
            # Display summary financials for the top stock
            top_data = ticker_data.get(selected_stock, {})
            if top_data:
                st.subheader(f"Summary Financials for {selected_stock}")
                try:
                    financials = top_data['financials']
                    info = top_data['info']
                    revenue = financials.loc['Total Revenue'][0] if 'Total Revenue' in financials.index else 'N/A'
                    ebitda = financials.loc['EBITDA'][0] if 'EBITDA' in financials.index else 'N/A'
                    pe = info.get('trailingPE', 'N/A')
                    market_cap = info.get('marketCap', 'N/A')
                    revenue_growth = info.get('revenueGrowth', 'N/A')
                    eps = info.get('earningsPerShare', 'N/A')
                    
                    financial_summary = {
                        "Yearly Revenue": revenue,
                        "EBITDA": ebitda,
                        "P/E Ratio": pe,
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
            @st.cache_data
            def fetch_daily_data(ticker):
                return yf.download(ticker, period="1y", interval="1d")
            
            top_stock = selected_stock
            top_stock_data = fetch_daily_data(top_stock)
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
                pattern_date = pattern['date']
                pattern_name = pattern['pattern']
                if pattern_date in top_stock_data.index:
                    price = top_stock_data.loc[pattern_date, 'High']
                    fig_candlestick.add_annotation(
                        x=pattern_date,
                        y=price,
                        xref="x",
                        yref="y",
                        text=pattern_name,
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=-40
                    )
            
            # Add technical indicators to the chart
            sma50 = ta.trend.SMAIndicator(close=top_stock_data['Close'], window=50)
            top_stock_data['SMA50'] = sma50.sma_indicator()
            sma200 = ta.trend.SMAIndicator(close=top_stock_data['Close'], window=200)
            top_stock_data['SMA200'] = sma200.sma_indicator()
            
            fig_candlestick.add_trace(go.Scatter(
                x=top_stock_data.index,
                y=top_stock_data['SMA50'],
                mode='lines',
                line=dict(color='blue', width=1),
                name='SMA 50'
            ))
            fig_candlestick.add_trace(go.Scatter(
                x=top_stock_data.index,
                y=top_stock_data['SMA200'],
                mode='lines',
                line=dict(color='orange', width=1),
                name='SMA 200'
            ))
            
            fig_candlestick.update_layout(
                height=800,
                width=1200,
                xaxis_rangeslider_visible=False,
                title=f"{top_stock} Price Chart with Technical Indicators",
                yaxis_title="Price (USD)"
            )
            
            st.plotly_chart(fig_candlestick, use_container_width=True)
            
            # Display RSI
            st.subheader(f"Relative Strength Index (RSI) for {top_stock}")
            rsi = ta.momentum.RSIIndicator(close=top_stock_data['Close'])
            top_stock_data['RSI'] = rsi.rsi()
            
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=top_stock_data.index,
                y=top_stock_data['RSI'],
                mode='lines',
                line=dict(color='purple', width=1),
                name='RSI'
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(
                height=300,
                width=1200,
                xaxis_title="Date",
                yaxis_title="RSI",
                showlegend=False
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

if __name__ == "__main__":
    main()
