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
