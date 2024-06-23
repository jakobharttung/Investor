import streamlit as st
import anthropic
import os
os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
my_api_key = st.secrets['ANTHROPIC_API_KEY']

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
  api_key = my_api_key
)
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
St.write(message.content)
