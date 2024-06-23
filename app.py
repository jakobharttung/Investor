import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import anthropic
from bs4 import BeautifulSoup
import os
import requests
# Streamlit app
st.title('Investor Analyst App')

os.environ["ANTHROPIC_API_KEY"] = "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"
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1000,
    temperature=0,
    system="You are a world-class poet. Respond only with short poems.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Why is the ocean salty?"
                }
            ]
        }
    ]
)
st.write(message.content)
