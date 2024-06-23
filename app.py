import streamlit as st
import anthropic
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
  api_key = "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"
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
