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
