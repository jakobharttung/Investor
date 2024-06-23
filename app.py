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
