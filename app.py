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
