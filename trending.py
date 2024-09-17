import pytz
from datetime import datetime, timedelta

# Function to get news for a company
def get_company_news(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    news = stock.news
    utc = pytz.UTC
    start_date = utc.localize(start_date)
    end_date = utc.localize(end_date)
    filtered_news = [n for n in news if start_date <= utc.localize(datetime.fromtimestamp(n['providerPublishTime'])) <= end_date]
    return filtered_news

# In the main app section, modify the crossover analysis loop:
for date, event_type in crossovers:
    start_date = date.replace(tzinfo=None) - timedelta(days=60)
    end_date = date.replace(tzinfo=None)
    news = get_company_news(ticker, start_date, end_date)
    
    analysis = analyze_crossover(date, event_type, news, company_info)
    
    st.write(f"**Event Date:** {date.strftime('%Y-%m-%d')}")
    st.write(f"**Event Type:** {'Upward' if event_type == 'up' else 'Downward'} Trend")
    st.write(f"**Analysis:**")
    st.write(analysis)
    st.write("---")
