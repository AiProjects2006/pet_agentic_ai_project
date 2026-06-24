from google import genai
import os
import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

try:
    with open("my_details.txt", "r", encoding="utf-8") as f:
        my_details = f.read()
except FileNotFoundError:
    my_details = "No personal details provided."


def get_response(message, history):
    history_text = ""

    # Handle Gradio history
    for msg in history:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                history_text += f"User: {content}\n"
            elif role == "assistant":
                history_text += f"Assistant: {content}\n"

    prompt = f"""
You are my personal AI assistant.

Use the following information about me to answer questions as if you are me.

Guidelines:
- Chat like you are me.
- Use my tone and style.
- Use my knowledge and personal information when relevant.
- Keep responses natural and casual.
- Don't mention that you're an AI unless asked.

About me:
{my_details}

Previous Conversation:
{history_text}

User Question:
{message}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Error: {str(e)}"


demo = gr.ChatInterface(
    fn=get_response,
    title="My Personal Chatbot"
)

if __name__ == "__main__":
    demo.launch()