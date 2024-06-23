import streamlit as st
from openai import OpenAI
client = OpenAI(api_key = "sk-proj-vzJUFCg293rnIAZKKo12T3BlbkFJn013xpp0JJbkI0zIbFOk")

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
  ]
)

st.write(completion.choices[0].message)
