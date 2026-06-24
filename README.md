# pet_agentic_ai_project
# My Personal Chatbot

My Personal Chatbot is a small Gradio app that turns Google Gemini into a personal assistant that answers in your voice, using local profile details from `my_details.txt`.

## Features

- Chat-style web UI built with Gradio
- Uses Google Gemini for responses
- Pulls personal context from a local text file
- Reads configuration from a `.env` file

## Requirements

- Python 3.10 or newer
- A Google Gemini API key

## Setup

1. Create and activate a virtual environment.
2. Install the dependencies:

   ```bash
   pip install google-genai gradio python-dotenv
   ```

3. Create a `.env` file in the project root with my API key:

   ```env
   GOOGLE_API_KEY=My_api_key_here
   ```

4. Add my personal profile text to `my_details.txt`.

## Run

Start the app with:

```bash
python app.py
```

Gradio will launch a local web app in my browser.

## Project Files

- `app.py` - main application entry point
- `my_details.txt` - personal context used to shape responses
- `.env` - local environment variables, including `GOOGLE_API_KEY`

## Notes

- If `my_details.txt` is missing, the app falls back to a default message.
- If `GOOGLE_API_KEY` is missing, the app raises an error at startup.
- The app currently uses the `gemini-2.5-flash` model.