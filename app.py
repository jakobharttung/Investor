import streamlit as st
import anthropic
# Streamlit app
st.title('Investor Analyst App')
import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="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"
)

message = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1000,
    temperature=0,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "tell me short poem on maths\n"
                }
            ]
        }
    ]
)
st.write(message.content)
